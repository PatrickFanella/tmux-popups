"""Project adapters use temporary repositories, notes, shells and coding tools."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import unittest
import test_launcher as launcher


class ProjectActionTests(unittest.TestCase):
    owned_cleanup = launcher.LauncherTests.owned_cleanup
    stub = launcher.LauncherTests.stub
    tmux = launcher.LauncherTests.tmux
    run_script = launcher.LauncherTests.run_script
    attach = launcher.LauncherTests.attach
    wait_until = launcher.LauncherTests.wait_until

    def setUp(self):
        launcher.LauncherTests.setUp(self)
        self.repo = self.home / "project ' with spaces"
        self.nested = self.repo / "src nested"
        self.nested.mkdir(parents=True)
        self.other = self.home / "non Git ' directory"
        self.other.mkdir()
        template = self.home / "git-template"
        template.mkdir()
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_TEMPLATE_DIR=str(template))
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], env=self.env, check=True)
        self.record = self.home / "tool-record"
        code = "import os,json,pathlib,sys; pathlib.Path("+repr(str(self.record))+").write_text(json.dumps({'cwd':os.getcwd(),'args':sys.argv[1:],'origin':os.environ.get('TMUX_POPUPS_DIRECTORY')}))"
        self.tool = self.stub("coding-tool", "exec python3 -c " + shlex.quote(code) + ' "$@"')
        code += "; pathlib.Path(sys.argv[1]).write_text('selected notes\\n')"
        self.editor = self.stub("editor", "exec python3 -c " + shlex.quote(code) + ' "$@"')

    def action(self, directory, *args, check=True, **variables):
        env = dict(self.env, TMUX_POPUPS_DIRECTORY=str(directory), **variables)
        return self.run_script("scripts/tools/project-action.sh", *args, env=env, input="", check=check)

    def test_git_status_uses_repository_root_and_non_git_fails_visibly(self):
        (self.repo / "root marker.txt").write_text("fixture\n")
        for directory in [self.repo, self.nested]:
            result = self.action(directory, "git")
            self.assertIn("No commits yet on main", result.stdout)
            self.assertIn('?? "root marker.txt"', result.stdout.splitlines())
        result = self.action(self.other, "git", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a git repository", result.stderr.lower())
        self.assertFalse((self.other / ".git").exists())

    def test_real_bash_stays_in_invoking_directory(self):
        for directory in [self.repo, self.nested, self.other]:
            result = self.action(directory, "shell", "-c", 'printf "%s" "$PWD"', SHELL="/bin/bash")
            self.assertEqual(result.stdout, str(directory))

    def test_coding_tool_root_fallback_and_exact_arguments(self):
        arguments = ["", "two words", "'quotes'", "$(not_executed)", "line\nend"]
        for directory, expected in [(self.repo, self.repo), (self.nested, self.repo), (self.other, self.other)]:
            self.action(directory, "code", str(self.tool), *arguments)
            self.assertEqual(json.loads(self.record.read_text()),
                             dict(cwd=str(expected), args=arguments, origin=str(directory)))

    def test_notes_created_only_on_selection_and_path_precedence(self):
        registry = self.home / "projects.tsv"
        registry.write_text((launcher.ROOT / "examples/popups.project.tsv").read_text())
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        self.run_script("scripts/list-popups.sh", "--execution-tsv")
        self.assertFalse((self.repo / "NOTES.md").exists())
        self.assertFalse(self.record.exists())
        self.action(self.nested, "notes", EDITOR=str(self.editor))
        self.assertEqual((self.repo / "NOTES.md").read_text(), "selected notes\n")
        self.action(self.nested, "notes", EDITOR=str(self.editor), TMUX_POPUPS_PROJECT_NOTES="docs ' notes/plan.md")
        self.assertTrue((self.repo / "docs ' notes/plan.md").exists())
        explicit = self.home / "outside ' notes/explicit.md"
        self.action(self.nested, "notes", str(explicit), EDITOR=str(self.editor), TMUX_POPUPS_PROJECT_NOTES="ignored.md")
        self.assertTrue(explicit.exists())
        self.assertFalse((self.repo / "ignored.md").exists())
        self.action(self.other, "notes", "~/home note.md", EDITOR=str(self.editor))
        self.assertTrue((self.home / "home note.md").exists())

    def test_missing_tool_or_editor_is_visible_and_does_not_create_notes(self):
        result = self.action(self.nested, "code", "missing_project_coder", check=False)
        self.assertEqual(result.returncode, 127)
        self.assertIn("missing_project_coder not found", result.stdout)
        note = self.repo / "missing parent/note.md"
        result = self.action(self.nested, "notes", str(note), EDITOR="missing_project_editor", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no usable editor", result.stderr)
        self.assertFalse(note.parent.exists())
        result = self.action(self.other, "unknown", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown project action", result.stderr)

    def test_git_root_and_notes_preserve_control_bytes(self):
        repository = self.home / "literal ' \\; $(no_exec) #{session_name}\t\n"
        repository.mkdir()
        nested = repository / "nested"
        nested.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(repository)], env=self.env, check=True)
        self.action(nested, "code", str(self.tool))
        self.assertEqual(json.loads(self.record.read_text())['cwd'], str(repository))
        note = "notes ' tab\t\n/name\n"
        self.action(nested, "notes", note, EDITOR=str(self.editor))
        self.assertEqual(json.loads(self.record.read_text())['args'], [str(repository / note)])
        self.assertTrue((repository / note).exists())

    def test_registry_dispatch_and_reuse_keep_project_and_origin_separate(self):
        code = "import os,json,pathlib,sys; pathlib.Path("+repr(str(self.record))+").write_text(json.dumps({'cwd':os.getcwd(),'args':sys.argv[1:],'origin':os.environ.get('TMUX_POPUPS_DIRECTORY')})); input('code-ready')"
        self.stub("coding-tool", "exec python3 -c " + shlex.quote(code) + ' "$@"')
        registry = self.home / "project-launch.tsv"
        text = (launcher.ROOT / "examples/popups.project.tsv").read_text()
        fields = ["project_code", "-", "4", "coding fixture", "90%", "85%",
                  "scripts/tools/project-action.sh", "window", "foreground", "on", "-", "plugin",
                  json.dumps(["code", str(self.tool), "two words", ""])]
        registry.write_text(text + "\t".join(fields) + "\n")
        self.tmux("set-option", "-g", "@tmux-popups-local-registry", str(registry))
        self.tmux("set-option", "-g", "@tmux-popups-project_code-reuse", "directory")
        self.attach()
        client = self.tmux("list-clients", "-F", "#{client_name}").stdout.strip()
        ids = self.tmux("display-message", "-p", "-t", "fixture", "#{session_id}|#{window_id}|#{pane_id}").stdout.strip().split("|")
        context = [client, *ids, str(self.nested)]
        self.run_script("scripts/run-popup.sh", "project_code", "--launch", *context)
        self.wait_until(self.record.exists)
        before = self.tmux("list-windows", "-t", "fixture", "-F", "#{window_id}").stdout
        self.assertEqual(len(before.splitlines()), 2)
        recorded = json.loads(self.record.read_text())
        self.assertEqual(recorded, dict(cwd=str(self.repo), args=["two words", ""], origin=str(self.nested)))
        modified = self.record.stat().st_mtime_ns
        self.run_script("scripts/run-popup.sh", "project_code", "--launch", *context)
        self.assertEqual(self.tmux("list-windows", "-t", "fixture", "-F", "#{window_id}").stdout, before)
        self.assertEqual(self.record.stat().st_mtime_ns, modified)

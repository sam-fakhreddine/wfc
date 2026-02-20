"""Tests for wfc.scripts.agents.documentation_agent — CRUD documentation agent."""

from __future__ import annotations


class TestDocumentationAction:
    def test_all_actions(self):
        from wfc.scripts.agents.documentation_agent import DocumentationAction

        assert DocumentationAction.CREATE.value == "create"
        assert DocumentationAction.UPDATE.value == "update"
        assert DocumentationAction.APPEND.value == "append"
        assert DocumentationAction.DELETE.value == "delete"

    def test_member_count(self):
        from wfc.scripts.agents.documentation_agent import DocumentationAction

        assert len(DocumentationAction) == 4


class TestValidatePayload:
    def test_valid_create_payload(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "create",
            "target_file": "docs/solutions/fix-auth.md",
            "content": "# Fix Auth\n\nSolution here.",
            "rationale": "Documenting auth fix from TASK-001",
            "generating_agent": "wfc-compound",
        }
        result = validate_payload(payload)
        assert result is not None
        assert result["action"] == "create"

    def test_valid_update_payload(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "update",
            "target_file": "docs/solutions/fix-auth.md",
            "content": "# Fix Auth v2\n\nUpdated solution.",
            "rationale": "Updated with new approach",
            "generating_agent": "wfc-compound",
        }
        result = validate_payload(payload)
        assert result is not None
        assert result["action"] == "update"

    def test_valid_append_payload(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "append",
            "target_file": "docs/solutions/fix-auth.md",
            "content": "\n## Additional Notes\n\nMore info here.",
            "rationale": "Adding follow-up notes",
            "generating_agent": "wfc-compound",
        }
        assert validate_payload(payload) is not None

    def test_valid_delete_payload(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "delete",
            "target_file": "docs/solutions/obsolete.md",
            "content": "",
            "rationale": "Document is obsolete after refactor",
            "generating_agent": "wfc-compound",
        }
        assert validate_payload(payload) is not None

    def test_missing_action_returns_none(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "target_file": "docs/x.md",
            "content": "x",
            "rationale": "x",
            "generating_agent": "x",
        }
        assert validate_payload(payload) is None

    def test_invalid_action_returns_none(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "destroy",
            "target_file": "docs/x.md",
            "content": "x",
            "rationale": "x",
            "generating_agent": "x",
        }
        assert validate_payload(payload) is None

    def test_missing_target_file_returns_none(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "create",
            "content": "x",
            "rationale": "x",
            "generating_agent": "x",
        }
        assert validate_payload(payload) is None

    def test_missing_rationale_returns_none(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "create",
            "target_file": "docs/x.md",
            "content": "x",
            "generating_agent": "x",
        }
        assert validate_payload(payload) is None

    def test_non_dict_returns_none(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        assert validate_payload("string") is None
        assert validate_payload(42) is None
        assert validate_payload(None) is None

    def test_path_traversal_rejected(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "create",
            "target_file": "../../../etc/passwd",
            "content": "x",
            "rationale": "x",
            "generating_agent": "x",
        }
        assert validate_payload(payload) is None

    def test_absolute_path_rejected(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "create",
            "target_file": "/etc/passwd",
            "content": "x",
            "rationale": "x",
            "generating_agent": "x",
        }
        assert validate_payload(payload) is None

    def test_non_docs_path_rejected(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "create",
            "target_file": "src/main.py",
            "content": "x",
            "rationale": "x",
            "generating_agent": "x",
        }
        assert validate_payload(payload) is None

    def test_defaults_generating_agent(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "create",
            "target_file": "docs/x.md",
            "content": "x",
            "rationale": "x",
        }
        result = validate_payload(payload)
        assert result is not None
        assert result["generating_agent"] == "unknown"

    def test_optional_workflow_id(self):
        from wfc.scripts.agents.documentation_agent import validate_payload

        payload = {
            "action": "create",
            "target_file": "docs/x.md",
            "content": "x",
            "rationale": "x",
            "generating_agent": "x",
            "workflow_id": "WF-001",
        }
        result = validate_payload(payload)
        assert result is not None
        assert result["workflow_id"] == "WF-001"


class TestDocumentationAgentExecute:
    def test_create_writes_file(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        payload = {
            "action": "create",
            "target_file": "docs/solutions/new-doc.md",
            "content": "# New Doc\n\nContent here.",
            "rationale": "test create",
            "generating_agent": "test",
        }
        result = agent.execute(payload)
        assert result["success"] is True
        assert (tmp_path / "docs" / "solutions" / "new-doc.md").exists()
        assert (
            tmp_path / "docs" / "solutions" / "new-doc.md"
        ).read_text() == "# New Doc\n\nContent here."

    def test_create_refuses_overwrite(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        target = tmp_path / "docs" / "existing.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("original")
        payload = {
            "action": "create",
            "target_file": "docs/existing.md",
            "content": "new content",
            "rationale": "test",
            "generating_agent": "test",
        }
        result = agent.execute(payload)
        assert result["success"] is False
        assert "exists" in result["error"].lower()
        assert target.read_text() == "original"

    def test_update_overwrites_existing(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        target = tmp_path / "docs" / "existing.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("old content")
        payload = {
            "action": "update",
            "target_file": "docs/existing.md",
            "content": "new content",
            "rationale": "test update",
            "generating_agent": "test",
        }
        result = agent.execute(payload)
        assert result["success"] is True
        assert target.read_text() == "new content"

    def test_update_fails_on_missing_file(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        payload = {
            "action": "update",
            "target_file": "docs/nonexistent.md",
            "content": "new content",
            "rationale": "test",
            "generating_agent": "test",
        }
        result = agent.execute(payload)
        assert result["success"] is False
        assert "not found" in result["error"].lower() or "does not exist" in result["error"].lower()

    def test_append_adds_to_existing(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        target = tmp_path / "docs" / "log.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Log\n\nEntry 1.")
        payload = {
            "action": "append",
            "target_file": "docs/log.md",
            "content": "\n\nEntry 2.",
            "rationale": "test append",
            "generating_agent": "test",
        }
        result = agent.execute(payload)
        assert result["success"] is True
        assert target.read_text() == "# Log\n\nEntry 1.\n\nEntry 2."

    def test_append_fails_on_missing_file(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        payload = {
            "action": "append",
            "target_file": "docs/nonexistent.md",
            "content": "appended content",
            "rationale": "test",
            "generating_agent": "test",
        }
        result = agent.execute(payload)
        assert result["success"] is False

    def test_delete_removes_file(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        target = tmp_path / "docs" / "obsolete.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("old stuff")
        payload = {
            "action": "delete",
            "target_file": "docs/obsolete.md",
            "content": "",
            "rationale": "obsolete",
            "generating_agent": "test",
        }
        result = agent.execute(payload)
        assert result["success"] is True
        assert not target.exists()

    def test_delete_fails_on_missing_file(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        payload = {
            "action": "delete",
            "target_file": "docs/nonexistent.md",
            "content": "",
            "rationale": "test",
            "generating_agent": "test",
        }
        result = agent.execute(payload)
        assert result["success"] is False

    def test_invalid_payload_returns_error(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        result = agent.execute({"garbage": True})
        assert result["success"] is False
        assert "invalid" in result["error"].lower() or "validation" in result["error"].lower()

    def test_result_has_audit_fields(self, tmp_path):
        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        payload = {
            "action": "create",
            "target_file": "docs/test.md",
            "content": "test",
            "rationale": "test audit",
            "generating_agent": "test-agent",
        }
        result = agent.execute(payload)
        assert result["success"] is True
        assert result["action"] == "create"
        assert result["target_file"] == "docs/test.md"
        assert result["generating_agent"] == "test-agent"
        assert "timestamp" in result


class TestObservabilityIntegration:
    def test_execute_emits_event(self, tmp_path):
        from unittest.mock import patch

        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        payload = {
            "action": "create",
            "target_file": "docs/test.md",
            "content": "test",
            "rationale": "test",
            "generating_agent": "test",
        }
        with patch("wfc.scripts.agents.documentation_agent._emit_doc_event") as mock_emit:
            agent.execute(payload)
            mock_emit.assert_called_once()
            assert mock_emit.call_args is not None

    def test_emit_never_raises(self, tmp_path):
        from unittest.mock import patch

        from wfc.scripts.agents.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(base_dir=tmp_path)
        payload = {
            "action": "create",
            "target_file": "docs/test.md",
            "content": "test",
            "rationale": "test",
            "generating_agent": "test",
        }
        with patch(
            "wfc.scripts.agents.documentation_agent._emit_doc_event",
            side_effect=RuntimeError("boom"),
        ):
            result = agent.execute(payload)
            assert result["success"] is True


class TestAllowedDirs:
    def test_docs_solutions_allowed(self):
        from wfc.scripts.agents.documentation_agent import ALLOWED_PREFIXES

        assert "docs/" in ALLOWED_PREFIXES
        assert "docs/solutions/" in ALLOWED_PREFIXES

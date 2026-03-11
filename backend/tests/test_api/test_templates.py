"""Tests for template CRUD routes and TemplateMember roundtrip.

Covers:
- Create / list / get / update / delete happy paths
- TemplateMember field preservation through JSON storage and retrieval
- Corrupted members_json falls back to empty list (not a 500)
- 404 for non-existent templates
"""
import json
import pytest

from app.models.council_template import CouncilTemplate


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

MEMBER_A = {
    "id": "m1",
    "provider": "openai",
    "model": "gpt-4o",
    "role": "Analyst",
    "archetype": "analytical",
    "custom_personality": "Be very precise.",
    "is_chair": True,
    "enable_thinking": False,
}

MEMBER_B = {
    "id": "m2",
    "provider": "anthropic",
    "model": "claude-3-sonnet",
    "role": "Creative",
    "archetype": "creative",
    "custom_personality": None,
    "is_chair": False,
    "enable_thinking": True,
}

SAVE_PAYLOAD = {
    "name": "Test Template",
    "description": "A template for testing",
    "members": [MEMBER_A, MEMBER_B],
}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class TestCreateTemplate:
    @pytest.mark.asyncio
    async def test_create_returns_201_or_200(self, client):
        response = await client.post("/api/templates", json=SAVE_PAYLOAD)
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_create_returns_id(self, client):
        response = await client.post("/api/templates", json=SAVE_PAYLOAD)
        data = response.json()
        assert "id" in data
        assert data["id"]  # non-empty

    @pytest.mark.asyncio
    async def test_create_preserves_name_and_description(self, client):
        response = await client.post("/api/templates", json=SAVE_PAYLOAD)
        data = response.json()
        assert data["name"] == "Test Template"
        assert data["description"] == "A template for testing"

    @pytest.mark.asyncio
    async def test_create_preserves_all_member_fields(self, client):
        """Every TemplateMember field must survive the POST → JSON → DB → response roundtrip."""
        response = await client.post("/api/templates", json=SAVE_PAYLOAD)
        data = response.json()
        members = data["members"]
        assert len(members) == 2

        chair = next(m for m in members if m["is_chair"])
        assert chair["id"] == "m1"
        assert chair["provider"] == "openai"
        assert chair["model"] == "gpt-4o"
        assert chair["role"] == "Analyst"
        assert chair["archetype"] == "analytical"
        assert chair["custom_personality"] == "Be very precise."
        assert chair["enable_thinking"] is False

        creative = next(m for m in members if not m["is_chair"])
        assert creative["enable_thinking"] is True
        assert creative["custom_personality"] is None

    @pytest.mark.asyncio
    async def test_create_without_description_accepted(self, client):
        payload = {**SAVE_PAYLOAD, "description": None}
        response = await client.post("/api/templates", json=payload)
        assert response.status_code in (200, 201)
        assert response.json()["description"] is None


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

class TestListTemplates:
    @pytest.mark.asyncio
    async def test_empty_list_initially(self, client):
        response = await client.get("/api/templates")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_created_templates_appear_in_list(self, client):
        await client.post("/api/templates", json=SAVE_PAYLOAD)
        await client.post("/api/templates", json={**SAVE_PAYLOAD, "name": "Second"})

        response = await client.get("/api/templates")
        data = response.json()
        assert len(data) == 2
        names = {t["name"] for t in data}
        assert "Test Template" in names
        assert "Second" in names

    @pytest.mark.asyncio
    async def test_list_includes_member_data(self, client):
        await client.post("/api/templates", json=SAVE_PAYLOAD)
        response = await client.get("/api/templates")
        template = response.json()[0]
        assert len(template["members"]) == 2


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------

class TestGetTemplate:
    @pytest.mark.asyncio
    async def test_get_existing_template(self, client):
        created = (await client.post("/api/templates", json=SAVE_PAYLOAD)).json()
        response = await client.get(f"/api/templates/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_404(self, client):
        response = await client.get("/api/templates/does-not-exist")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_preserves_member_fields(self, client):
        created = (await client.post("/api/templates", json=SAVE_PAYLOAD)).json()
        response = await client.get(f"/api/templates/{created['id']}")
        members = response.json()["members"]
        chair = next(m for m in members if m["is_chair"])
        assert chair["custom_personality"] == "Be very precise."


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

class TestUpdateTemplate:
    @pytest.mark.asyncio
    async def test_update_name(self, client):
        created = (await client.post("/api/templates", json=SAVE_PAYLOAD)).json()
        updated_payload = {**SAVE_PAYLOAD, "name": "Renamed Template"}
        response = await client.put(f"/api/templates/{created['id']}", json=updated_payload)
        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Template"

    @pytest.mark.asyncio
    async def test_update_members(self, client):
        created = (await client.post("/api/templates", json=SAVE_PAYLOAD)).json()
        new_members = [{**MEMBER_A, "model": "gpt-4-turbo"}]
        response = await client.put(
            f"/api/templates/{created['id']}",
            json={**SAVE_PAYLOAD, "members": new_members}
        )
        assert response.status_code == 200
        members = response.json()["members"]
        assert len(members) == 1
        assert members[0]["model"] == "gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_404(self, client):
        response = await client.put("/api/templates/no-such-id", json=SAVE_PAYLOAD)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class TestDeleteTemplate:
    @pytest.mark.asyncio
    async def test_delete_existing(self, client):
        created = (await client.post("/api/templates", json=SAVE_PAYLOAD)).json()
        response = await client.delete(f"/api/templates/{created['id']}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_deleted_template_not_in_list(self, client):
        created = (await client.post("/api/templates", json=SAVE_PAYLOAD)).json()
        await client.delete(f"/api/templates/{created['id']}")
        response = await client.get("/api/templates")
        ids = [t["id"] for t in response.json()]
        assert created["id"] not in ids

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client):
        response = await client.delete("/api/templates/ghost-id")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Corrupted JSON resilience
# ---------------------------------------------------------------------------

class TestCorruptedMembersJson:
    @pytest.mark.asyncio
    async def test_corrupted_json_returns_empty_members_not_500(self, test_db, client):
        """If members_json in the DB is corrupted, the list endpoint must still
        return 200 with empty members instead of crashing with a 500."""
        import uuid
        bad_template = CouncilTemplate(
            id=str(uuid.uuid4()),
            name="Corrupted",
            description=None,
            members_json="not valid json {{{",
        )
        test_db.add(bad_template)
        await test_db.commit()

        response = await client.get("/api/templates")
        assert response.status_code == 200

        templates = response.json()
        corrupted = next(t for t in templates if t["name"] == "Corrupted")
        assert corrupted["members"] == [], (
            "Corrupted JSON must fall back to [] not crash the request"
        )

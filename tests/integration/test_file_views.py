import io

import pytest

from src.core.exception import InvalidInputException

pytestmark = pytest.mark.asyncio

@pytest.mark.integration
class TestFileEndpoints:
    """Интеграционные тесты для эндпоинтов, работающих с файлами."""

    async def test_upload_file_to_task_valid_file_succeeds(self, client, auth_headers, test_task):
        """Тест успешной загрузки валидного файла к задаче."""
        file_content = b"Test file content"
        files = {"uploaded_file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        response = await client.post(
            f"/tasks/{test_task.id}/file", files=files, headers=auth_headers
        )
        assert response.status_code == 200
        assert "успешно загружен" in response.json()["msg"]

    async def test_get_task_file_for_existing_file_succeeds(self, client, auth_headers, test_task, db_session):
        """Тест успешного получения ранее загруженного файла задачи."""
        file_content = b"Test file content"
        test_task.file_data = file_content
        test_task.file_name = "test.txt"
        await db_session.commit()
        response = await client.get(
            f"/tasks/{test_task.id}/file", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.content == file_content
        assert 'filename=test.txt' in response.headers["content-disposition"]

    async def test_upload_file_with_invalid_extension_returns_400(self, client, auth_headers, test_task):
        """Тест загрузки файла с недопустимым расширением должен вернуть 400."""
        extension = ".exe"
        file_content = b"malicious content"
        files = {"uploaded_file": (f"test{extension}", io.BytesIO(file_content), "application/x-executable")}
        response = await client.post(
            f"/tasks/{test_task.id}/file", files=files, headers=auth_headers
        )
        data = response.json()
        assert response.status_code == 400
        assert data["error_code"] == "INVALID_INPUT"
        assert data["detail"]["field_name"] == "расширение файла"

    async def test_upload_empty_file_returns_400(self, client, auth_headers, test_task):
        """Тест загрузки пустого файла должен вернуть 400."""
        files = {"uploaded_file": ("empty.txt", io.BytesIO(b""), "text/plain")}
        response = await client.post(
            f"/tasks/{test_task.id}/file", files=files, headers=auth_headers
        )
        json_data = response.json()
        assert response.status_code == 400
        assert json_data["error_code"] == "INVALID_INPUT"
        assert json_data["detail"]["field_name"] == "файл"
        assert "пустой файл" in json_data["detail"]["provided_value"]

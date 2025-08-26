import io

import pytest

from src.core.exception import InvalidInputException


class TestFileEndpoints:
    """Интеграционные тесты работы с файлами."""

    def test_upload_file_to_task(self, client, auth_headers, test_task):
        """Тест загрузки файла к задаче."""
        file_content = b"Test file content"
        files = {
            "uploaded_file": ("test.txt", io.BytesIO(file_content), "text/plain")
        }

        response = client.post(
            f"/tasks/{test_task.id}/file",
            files=files,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "успешно загружен" in data["msg"]

    def test_get_task_file(self, client, auth_headers, test_task, db_session):
        """Тест получения файла задачи."""
        # Сначала загружаем файл
        test_task.file_data = b"Test file content"
        test_task.file_name = "test.txt"
        db_session.commit()

        response = client.get(
            f"/tasks/{test_task.id}/file", headers=auth_headers)

        assert response.status_code == 200
        assert response.content == b"Test file content"

    def test_upload_file_invalid_extension(self, client, auth_headers, test_task):
        """Тест загрузки файла с недопустимым расширением."""
        extension = ".exe"
        file_content = b"Test file content"
        files = {
            "uploaded_file": (f"test{extension}", io.BytesIO(file_content), "application/x-executable")
        }
        with pytest.raises(Exception) as exc_info:
            client.post(
                f"/tasks/{test_task.id}/file",
                files=files,
                headers=auth_headers
            )

        assert InvalidInputException(
            "расширение файла", extension, "допустимое расширение") == exc_info.value

    def test_upload_empty_file(self, client, auth_headers, test_task):
        """Тест загрузки пустого файла."""
        files = {
            "uploaded_file": ("empty.txt", io.BytesIO(b""), "text/plain")
        }
        with pytest.raises(Exception) as exc_info:
            client.post(
                f"/tasks/{test_task.id}/file",
                files=files,
                headers=auth_headers
            )

        assert InvalidInputException(
            "файл", "пустой файл", "непустой файл") == exc_info.value

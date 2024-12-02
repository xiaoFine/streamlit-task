import pytest
from unittest.mock import MagicMock, patch
from streamlit_task.scheduler import Scheduler, CeleryScheduler

class TestScheduler:
    def test_init_with_email_config(self, mock_email_config):
        scheduler = Scheduler(email_config=mock_email_config)
        assert scheduler.email_config == mock_email_config

    def test_send_email_notification(self, mock_email_config, mock_smtp):
        scheduler = Scheduler(email_config=mock_email_config)
        scheduler._send_email_notification(
            task_name="test_task",
            recipient="recipient@example.com",
            status="completed",
            result="success"
        )
        
        # 验证是否正确调用了SMTP方法
        mock_smtp.return_value.__enter__.return_value.sendmail.assert_called_once()

class TestCeleryScheduler:
    def test_init_without_celery(self):
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError) as exc_info:
                CeleryScheduler()
            assert "Celery SDK is not installed" in str(exc_info.value)

    @patch('celery.Celery')
    def test_init_with_celery(self, mock_celery, mock_email_config):
        scheduler = CeleryScheduler(
            broker_url='redis://localhost:6379/0',
            email_config=mock_email_config
        )
        assert scheduler.email_config == mock_email_config
        mock_celery.assert_called_once()

    @patch('celery.Celery')
    def test_register_task(self, mock_celery, mock_email_config):
        scheduler = CeleryScheduler(
            broker_url='redis://localhost:6379/0',
            email_config=mock_email_config
        )
        
        # 创建测试任务
        @scheduler.register(notify_email='test@example.com')
        def test_task():
            return "test result"

        # 验证任务是否正确注册
        mock_celery.return_value.task.assert_called_once() 
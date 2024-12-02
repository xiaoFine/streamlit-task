class Scheduler:
    def __init__(self, email_config=None):
        """
        调度器基类
        Args:
            email_config: 邮件配置，格式为 {
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'sender': 'sender@example.com',
                'password': 'your_password'
            }
        """
        self.email_config = email_config

    def _send_email_notification(self, task_name, recipient, status, result=None):
        """发送邮件通知"""
        if not self.email_config:
            return
        
        import smtplib
        from email.mime.text import MIMEText
        from email.header import Header
        
        subject = f'Task {task_name} {status}'
        content = f'Task {task_name} has {status}.\n'
        if result:
            content += f'Result: {result}'
            
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = self.email_config['sender']
        msg['To'] = recipient
        
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender'], self.email_config['password'])
                server.sendmail(self.email_config['sender'], [recipient], msg.as_string())
        except Exception as e:
            print(f"Failed to send email notification: {e}")

    def register(self, func):
        """基础装饰器方法"""
        raise NotImplementedError

class CeleryScheduler(Scheduler):
    def __init__(self, broker_url='redis://localhost:6379/0', backend_url=None, 
                 email_config=None, **celery_configs):
        """
        初始化 Celery 调度器
        Args:
            broker_url: Celery broker 地址
            backend_url: Celery 结果后端地址
            email_config: 邮件配置
            celery_configs: 其他 Celery 配置参数
        """
        super().__init__(email_config)
        
        try:
            from celery import Celery
        except ImportError:
            raise RuntimeError("Celery SDK is not installed. Please install it to use CeleryScheduler.")
        
        self.app = Celery('tasks',
                         broker=broker_url,
                         backend=backend_url)
        
        self.app.conf.update(
            task_serializer='json',
            result_serializer='json',
            accept_content=['json'],
            **celery_configs
        )

    def register(self, notify_email=None, *args, **kwargs):
        """
        Celery任务注册装饰器
        Args:
            notify_email: 任务完成后通知的邮箱地址
            *args, **kwargs: 传递给 Celery task 装饰器的参数
        """
        def decorator(func):
            # 注册任务完成的回调
            def success_callback(result):
                if notify_email:
                    self._send_email_notification(func.__name__, notify_email, "completed", result)
            
            def error_callback(exc):
                if notify_email:
                    self._send_email_notification(func.__name__, notify_email, "failed", str(exc))
            
            # 将函数注册为 Celery 任务
            task = self.app.task(func, *args, **kwargs)
            
            def wrapper(*args, **kwargs):
                # 异步执行任务并添加回调
                result = task.delay(*args, **kwargs)
                result.then(success_callback, error_callback)
                return result
            
            return wrapper
        return decorator
    


from fastapi import HTTPException
from pydantic import EmailStr
from typing import Optional, Dict, Any
import os
import asyncio
import httpx
import logging
from httpx import ConnectError, ReadTimeout

class EmailTemplates:
    """電子郵件範本管理類"""
    
    @staticmethod
    def verification_email(verification_url: str) -> str:
        """
        產生驗證郵件的 HTML 內容
        
        Args:
            verification_url (str): 驗證連結網址
            
        Returns:
            str HTML 格式的郵件內容
        """
        return f'''
        <html>
          <body>
            <h2>歡迎註冊！</h2>
            <p>請點擊下方連結驗證您的電子郵件：</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            <p>此連結將在 24 小時後失效。</p>
          </body>
        </html>
        '''

    @staticmethod
    def reset_password_email(reset_url: str) -> str:
        """
        產生重設密碼郵件的 HTML 內容
        
        Args:
            reset_url (str): 重設密碼的連結網址
            
        Returns:
            str: HTML 格式的郵件內容
        """
        return f'''
        <html>
          <body>
            <h2>重設密碼請求</h2>
            <p>我們收到了您重設密碼的請求。如果這不是您本人的操作，請忽略此郵件。</p>
            <p>請點擊下方連結重設您的密碼：</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>此連結將在 1 小時後失效。</p>
          </body>
        </html>
        '''

class EmailService:
    """電子郵件服務類"""

    def __init__(self):
        """初始化電子郵件服務"""
        self.service_host = os.getenv("EMAIL_SERVICE_HOST")
        self.service_port = os.getenv("EMAIL_SERVICE_PORT")
        if not self.service_host or not self.service_port:
            raise ValueError("未設定郵件服務位址或端口")
        self.base_url = f"http://{self.service_host}:{self.service_port}"
        # 設置詳細的超時配置
        self.connect_timeout = 5.0  # 連接超時時間
        self.read_timeout = 10.0    # 讀取超時時間
        self.write_timeout = 10.0   # 寫入超時時間
        self.max_retries = 2

    async def send_email(
        self,
        to_email: EmailStr,
        subject: str,
        html_content: str,
        custom_headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> None:
        """
        發送電子郵件的通用方法
        
        Args:
            to_email: 收件人地址
            subject: 郵件主旨
            html_content: HTML 格式的郵件內容
            custom_headers: 自定義的郵件標頭
            retry_count: 目前重試次數
            
        Raises:
            HTTPException: 當郵件發送失敗時拋出 500 錯誤
        """
        payload = {
            "to": [str(to_email)],
            "subject": subject,
            "body": html_content
        }

        try:
            # 如果是重試，添加延遲
            if retry_count > 0:
                await asyncio.sleep(1 * retry_count)  # 隨著重試次數增加延遲
                
            # 使用詳細的超時配置
            timeout_config = httpx.Timeout(
                connect=self.connect_timeout,
                read=self.read_timeout,
                write=self.write_timeout,
                pool=None
            )
            
            async with httpx.AsyncClient(
                timeout=timeout_config,
                verify=False  # 允許自簽名證書，僅用於開發環境
            ) as client:
                logging.info(f"嘗試連接郵件服務 {self.base_url} (重試次數: {retry_count})")
                response = await client.post(
                    f"{self.base_url}/send-email",
                    json=payload
                )
                
                if response.status_code != 200:
                    error_json = await response.json()
                    error_detail = error_json.get("error", "未知錯誤")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"郵件服務錯誤: {error_detail}"
                    )

        except (ConnectError, ReadTimeout) as e:
            error_msg = (
                f"郵件服務連接失敗 (嘗試次數: {retry_count + 1}/{self.max_retries + 1})\n"
                f"目標地址: {self.base_url}\n"
                f"錯誤詳情: {str(e)}"
            )
            logging.error(f"{error_msg}: {str(e)}")
            if retry_count < self.max_retries:
                return await self.send_email(
                    to_email,
                    subject,
                    html_content,
                    custom_headers,
                    retry_count + 1
                )
            raise HTTPException(status_code=500, detail=error_msg)
            
        except asyncio.TimeoutError:
            error_msg = (
                f"發送郵件超時\n"
                f"目標地址: {self.base_url}\n"
                f"連接超時: {self.connect_timeout}秒\n"
                f"讀取超時: {self.read_timeout}秒"
            )
            logging.error(f"{error_msg} (嘗試次數: {retry_count + 1}/{self.max_retries + 1})")
            if retry_count < self.max_retries:
                return await self.send_email(
                    to_email,
                    subject,
                    html_content,
                    custom_headers,
                    retry_count + 1
                )
            raise HTTPException(status_code=500, detail=f"{error_msg}，請稍後再試")
            
        except Exception as e:
            error_msg = (
                f"發送郵件時發生錯誤\n"
                f"目標地址: {self.base_url}\n"
                f"錯誤類型: {e.__class__.__name__}\n"
                f"錯誤詳情: {str(e)}"
            )
            logging.error(f"{error_msg} (嘗試次數: {retry_count + 1}/{self.max_retries + 1})")
            if retry_count < self.max_retries:
                return await self.send_email(
                    to_email,
                    subject,
                    html_content,
                    custom_headers,
                    retry_count + 1
                )
            raise HTTPException(status_code=500, detail=error_msg)

    async def send_verification_email(
        self,
        to_email: EmailStr,
        token: str,
        base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    ) -> None:
        """
        發送電子郵件驗證信
        
        Args:
            to_email: 收件人地址
            token: 驗證 token
            base_url: 網站基礎 URL
        """
        verification_url = f"{base_url}/user/verify-email/{token}"
        html_content = EmailTemplates.verification_email(verification_url)
        
        await self.send_email(
            to_email=to_email,
            subject="驗證您的電子郵件",
            html_content=html_content
        )

    async def send_password_reset_email(
        self,
        to_email: EmailStr,
        token: str,
        base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    ) -> None:
        """
        發送重設密碼郵件
        
        Args:
            to_email: 收件人地址
            token: 重設密碼用的 token
            base_url: 網站基礎 URL
        """
        reset_url = f"{base_url}/user/reset-password/{token}"
        html_content = EmailTemplates.reset_password_email(reset_url)
        
        await self.send_email(
            to_email=to_email,
            subject="重設您的密碼",
            html_content=html_content
        )

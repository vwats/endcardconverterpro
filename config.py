import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration with validation."""
    PRODUCTION: bool
    SERVER_NAME: Optional[str]
    SESSION_SECRET: str
    STRIPE_SECRET_KEY: Optional[str]
    STRIPE_PUBLISHABLE_KEY: Optional[str]
    DATABASE_URL: Optional[str]
    FLASK_DEBUG: bool
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER: str = '/tmp/uploads'

    @classmethod
    def from_env(cls) -> 'Config':
        """Create configuration from environment variables with validation."""
        production = bool(os.environ.get('PRODUCTION'))
        
        # Required in production
        if production:
            required_vars = ['SERVER_NAME', 'SESSION_SECRET', 'STRIPE_SECRET_KEY', 'STRIPE_PUBLISHABLE_KEY']
            missing = [var for var in required_vars if not os.environ.get(var)]
            if missing:
                raise ValueError(f"Missing required environment variables in production: {', '.join(missing)}")

        return cls(
            PRODUCTION=production,
            SERVER_NAME=os.environ.get('SERVER_NAME'),
            SESSION_SECRET=os.environ.get('SESSION_SECRET', 'dev_secret_key'),
            STRIPE_SECRET_KEY=os.environ.get('STRIPE_SECRET_KEY'),
            STRIPE_PUBLISHABLE_KEY=os.environ.get('STRIPE_PUBLISHABLE_KEY'),
            DATABASE_URL=os.environ.get('DATABASE_URL'),
            FLASK_DEBUG=bool(os.environ.get('FLASK_DEBUG')),
        )

    def validate(self) -> None:
        """Perform additional validation on configuration values."""
        if self.PRODUCTION:
            if not self.SERVER_NAME:
                raise ValueError("SERVER_NAME is required in production")
            if not self.SESSION_SECRET or self.SESSION_SECRET == 'dev_secret_key':
                raise ValueError("Secure SESSION_SECRET is required in production")
            if not self.STRIPE_SECRET_KEY or not self.STRIPE_PUBLISHABLE_KEY:
                raise ValueError("Stripe API keys are required in production")
        
        # Validate upload folder
        if not os.path.exists(self.UPLOAD_FOLDER):
            try:
                os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
            except Exception as e:
                raise ValueError(f"Cannot create upload folder: {str(e)}")
        
        if not os.access(self.UPLOAD_FOLDER, os.W_OK):
            raise ValueError(f"Upload folder {self.UPLOAD_FOLDER} is not writable")

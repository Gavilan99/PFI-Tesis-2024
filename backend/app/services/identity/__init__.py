from app.services.identity.base import IdentityProvider, IdentityUser, IssuedToken
from app.services.identity.cognito import CognitoIdentityProvider
from app.services.identity.local import LocalIdentityProvider

__all__ = [
    "CognitoIdentityProvider",
    "IdentityProvider",
    "IdentityUser",
    "IssuedToken",
    "LocalIdentityProvider",
    "build_identity_provider",
]


def build_identity_provider(config) -> IdentityProvider:
    if config.IDENTITY_PROVIDER == "cognito":
        return CognitoIdentityProvider(
            region=config.COGNITO_REGION,
            user_pool_id=config.COGNITO_USER_POOL_ID,
            client_id=config.COGNITO_APP_CLIENT_ID,
        )
    return LocalIdentityProvider()

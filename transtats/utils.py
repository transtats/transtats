"""
Some base utilities/classes.
"""

from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class TranstatsOIDCBackend(OIDCAuthenticationBackend):
    def filter_users_by_claims(self, claims):
        """Find users by matching username=sub."""
        # The claims.get and None-case were dropped, since if there is no sub,
        # the OpenID Connect specification was broken.
        return self.UserModel.objects.filter(username=claims['sub'])

    def create_user(self, claims):
        """ Create a new user from the retrieved claims. """
        email = claims.get('email')

        return self.UserModel.objects.create_user(claims['sub'], email=email)

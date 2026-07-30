from flask import redirect, request


def register_request_hooks(app):
    @app.before_request
    def handle_all():
        if request.endpoint and request.endpoint.startswith("webhook."):
            return None

        user_agent = request.headers.get("User-Agent", "").lower()
        if "facebookexternalhit" in user_agent or "facebot" in user_agent:
            return None

        if request.headers.get("X-Forwarded-Proto", "http") != "https":
            return redirect(request.url.replace("http://", "https://"), code=301)

    @app.before_request
    def force_domain():
        if request.endpoint and request.endpoint.startswith("webhook."):
            return None

        url = request.url
        if request.headers.get("X-Forwarded-Proto", "http") != "https":
            url = url.replace("http://", "https://")

        if not request.host.startswith("www."):
            url = url.replace("://", "://www.")

        if url != request.url:
            return redirect(url, code=301)

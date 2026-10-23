import os
from urllib.parse import urlencode

import requests
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import TemplateView


TMDB_API_URL = "https://api.themoviedb.org/3"


def _tmdb_headers():
    token = os.getenv("TMDB_API_TOKEN", "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzZmI1YjQxZmNjNTczMmRkYzVjNmIyYWRhZmExMjgxMCIsIm5iZiI6MTc3NzU0OTYxMS4zOTkwMDAyLCJzdWIiOiI2OWYzNDEyYjFmMzJmMWE3MjhlYWJmMDgiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.OWaJB5le0mYIzhd7hZ5xhWPJQcTFayU92FQU3GQLSys").strip()
    if not token:
        return None

    return {
        "Authorization": f"Bearer {token}",
        "accept": "application/json",
    }


def _api_error_message(exc):
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        status_code = exc.response.status_code
        if status_code in (401, 403):
            return "O TMDB recusou o token. Configure um Read Access Token valido."
        if status_code == 429:
            return "O limite de requisicoes do TMDB foi atingido. Tente novamente mais tarde."
        return f"O TMDB retornou o erro HTTP {status_code} ao buscar dados."

    if isinstance(exc, requests.RequestException):
        return "Nao foi possivel conectar ao TMDB. Verifique sua conexao com a internet."

    return "O TMDB retornou uma resposta invalida."


class IndexView(TemplateView):
    template_name = "pagina/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            page = max(1, min(int(self.request.GET.get("page", "1")), 500))
        except ValueError:
            page = 1

        context.update(
            {
                "lista_filmes": [],
                "mensagem": "",
                "pagina_atual": page,
            }
        )

        headers = _tmdb_headers()
        if headers is None:
            context["mensagem"] = (
                "Configure a variavel de ambiente TMDB_API_TOKEN para buscar filmes."
            )
            return context

        try:
            response = requests.get(
                f"{TMDB_API_URL}/movie/popular",
                headers=headers,
                params={"language": "pt-BR", "page": page},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and isinstance(data.get("results"), list):
                context["lista_filmes"] = data["results"]
            else:
                context["mensagem"] = "A API do TMDB retornou dados inesperados."
        except (requests.RequestException, ValueError) as exc:
            context["mensagem"] = _api_error_message(exc)
            print(f"Erro ao buscar filmes no TMDB: {exc}")

        return context


def assistir_trailer(request, movie_id):
    headers = _tmdb_headers()
    if headers is None:
        messages.error(request, "Configure TMDB_API_TOKEN para abrir os trailers.")
        return redirect("inicio")

    try:
        videos = []
        for language in ("pt-BR", "en-US"):
            response = requests.get(
                f"{TMDB_API_URL}/movie/{movie_id}/videos",
                headers=headers,
                params={
                    "language": language,
                    "include_video_language": "pt,en,null",
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and isinstance(data.get("results"), list):
                videos = data["results"]
            if videos:
                break
    except (requests.RequestException, ValueError) as exc:
        print(f"Erro ao buscar trailer do filme {movie_id} no TMDB: {exc}")
        messages.error(request, _api_error_message(exc))
        return redirect("inicio")

    youtube_videos = [
        video
        for video in videos
        if isinstance(video, dict)
        and video.get("site") == "YouTube"
        and video.get("key")
    ]
    trailer = next(
        (
            video
            for video in youtube_videos
            if video.get("type") == "Trailer" and video.get("official")
        ),
        None,
    )
    if trailer is None:
        trailer = next(
            (video for video in youtube_videos if video.get("type") == "Trailer"),
            None,
        )
    if trailer is None:
        trailer = next(
            (
                video
                for video in youtube_videos
                if video.get("type") == "Teaser" and video.get("official")
            ),
            None,
        )
    if trailer is None:
        messages.warning(request, "Este filme ainda nao tem trailer disponivel.")
        return redirect("inicio")

    trailer_url = "https://www.youtube.com/watch?" + urlencode(
        {"v": trailer["key"]}
    )
    return redirect(trailer_url)

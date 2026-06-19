from sqlmodel import Session, select

from app.models import DigitalHumanProfile, PostProcessTemplate, VoiceProfile


def seed_defaults(session: Session) -> None:
    if session.exec(select(DigitalHumanProfile)).first() is None:
        session.add(
            DigitalHumanProfile(
                name="Default Presenter",
                preview_image_path="/static/default-presenter.png",
                source_media_path="/static/default-presenter.mp4",
                renderer_adapter_key="mock-avatar",
            )
        )

    if session.exec(select(VoiceProfile)).first() is None:
        session.add(
            VoiceProfile(
                name="Default Voice",
                provider_key="mock-tts",
                voice_key="default",
                style_tags=["neutral", "mandarin"],
                is_default=True,
            )
        )

    if session.exec(select(PostProcessTemplate)).first() is None:
        session.add(
            PostProcessTemplate(
                name="Default Vertical Video",
                subtitle_style={"font_size": 42, "position": "bottom"},
                cover_strategy="first_frame",
            )
        )

    session.commit()

from sqlmodel import Session, select

from app.models import DigitalHumanProfile, PostProcessTemplate, VoiceProfile


def seed_defaults(session: Session) -> None:
    default_human = session.exec(
        select(DigitalHumanProfile).where(DigitalHumanProfile.name == "Default Presenter")
    ).first()
    if default_human is None:
        session.add(
            DigitalHumanProfile(
                name="Default Presenter",
                preview_image_path="/static/default-presenter.png",
                source_media_path="/static/default-presenter.mp4",
                renderer_adapter_key="mock-avatar",
            )
        )

    default_voice = session.exec(
        select(VoiceProfile).where(VoiceProfile.is_default.is_(True))
    ).first()
    if default_voice is None:
        session.add(
            VoiceProfile(
                name="Default Voice",
                provider_key="mock-tts",
                voice_key="default",
                style_tags=["neutral", "mandarin"],
                is_default=True,
            )
        )

    default_template = session.exec(
        select(PostProcessTemplate).where(PostProcessTemplate.name == "Default Vertical Video")
    ).first()
    if default_template is None:
        session.add(
            PostProcessTemplate(
                name="Default Vertical Video",
                subtitle_style={"font_size": 42, "position": "bottom"},
                cover_strategy="first_frame",
            )
        )

    session.commit()

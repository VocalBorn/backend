
import uuid
import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel, create_engine
from enum import Enum
from src.course.models import Situation, Chapter, Sentence, SpeakerRole
from src.shared.config.config import Settings, get_settings

# 導入所有模型以確保關聯正確建立
from src.auth.models import Account, EmailVerification, User, UserWord
from src.practice.models import PracticeSession, PracticeRecord, PracticeFeedback, PracticeSessionFeedback
from src.therapist.models import TherapistProfile, TherapistClient
from src.pairing.models import PairingToken
from src.verification.models import TherapistApplication, UploadedDocument
from src.ai_analysis.models import AIAnalysisTask, AIAnalysisResult, TaskStatus


# --- Seed Data Generation ---

def create_seed_data():
    """Generates seed data for situations, chapters, and sentences."""

    # 1. Situation: 餐廳用餐 (Hospital Cafeteria)
    situation1 = Situation(
        situation_name="餐廳用餐",
        description="學習如何在醫院餐廳用餐",
        location="醫院餐廳"
    )

    chapter1_1 = Chapter(situation=situation1, chapter_name="尋找座位與點餐", sequence_number=1)
    sentences1_1 = [
        Sentence(chapter=chapter1_1, sentence_name="詢問餐點", speaker_role=SpeakerRole.SELF, role_description="使用者", content="請問今天的特餐是什麼？"),
        Sentence(chapter=chapter1_1, sentence_name="回覆餐點", speaker_role=SpeakerRole.OTHER, role_description="餐廳工作人員", content="今天的特餐是清蒸魚套餐。"),
        Sentence(chapter=chapter1_1, sentence_name="點餐", speaker_role=SpeakerRole.SELF, role_description="使用者", content="好的，我想要一份特餐。"),
    ]

    chapter1_2 = Chapter(situation=situation1, chapter_name="取餐與付款", sequence_number=2)
    sentences1_2 = [
        Sentence(chapter=chapter1_2, sentence_name="取餐", speaker_role=SpeakerRole.OTHER, role_description="餐廳工作人員", content="您的餐點好了，請到這邊取餐。"),
        Sentence(chapter=chapter1_2, sentence_name="詢問付款", speaker_role=SpeakerRole.SELF, role_description="使用者", content="請問總共多少錢？"),
        Sentence(chapter=chapter1_2, sentence_name="告知金額", speaker_role=SpeakerRole.OTHER, role_description="餐廳工作人員", content="總共是150元。"),
    ]

    # 2. Situation: 醫院就診 (Hospital Visit)
    situation2 = Situation(
        situation_name="醫院就診",
        description="學習如何在醫院就診",
        location="醫院"
    )

    chapter2_1 = Chapter(situation=situation2, chapter_name="掛號與報到", sequence_number=1)
    sentences2_1 = [
        Sentence(chapter=chapter2_1, sentence_name="掛號", speaker_role=SpeakerRole.SELF, role_description="病患", content="你好，我要掛號，看心臟內科。"),
        Sentence(chapter=chapter2_1, sentence_name="確認身份", speaker_role=SpeakerRole.OTHER, role_description="掛號櫃台人員", content="好的，請給我您的健保卡。"),
        Sentence(chapter=chapter2_1, sentence_name="完成掛號", speaker_role=SpeakerRole.OTHER, role_description="掛號櫃台人員", content="這是您的號碼牌，請到二樓診間稍等。"),
    ]

    chapter2_2 = Chapter(situation=situation2, chapter_name="看診過程", sequence_number=2)
    sentences2_2 = [
        Sentence(chapter=chapter2_2, sentence_name="醫師問診", speaker_role=SpeakerRole.OTHER, role_description="醫師", content="請問您哪裡不舒服？"),
        Sentence(chapter=chapter2_2, sentence_name="描述症狀", speaker_role=SpeakerRole.SELF, role_description="病患", content="我最近常常覺得胸悶。"),
        Sentence(chapter=chapter2_2, sentence_name="醫師建議", speaker_role=SpeakerRole.OTHER, role_description="醫師", content="我們先做個心電圖檢查看看。"),
    ]

    chapter2_3 = Chapter(situation=situation2, chapter_name="批價與領藥", sequence_number=3)
    sentences2_3 = [
        Sentence(chapter=chapter2_3, sentence_name="批價", speaker_role=SpeakerRole.SELF, role_description="病患", content="你好，我要繳費。"),
        Sentence(chapter=chapter2_3, sentence_name="領藥", speaker_role=SpeakerRole.OTHER, role_description="藥師", content="王先生，您的藥好了。"),
        Sentence(chapter=chapter2_3, sentence_name="確認藥物", speaker_role=SpeakerRole.SELF, role_description="病患", content="謝謝，請問這個藥怎麼吃？"),
    ]


    # 3. Situation: 購物付款 (Shopping Payment)
    situation3 = Situation(
        situation_name="購物付款",
        description="學習如何在商店付款",
        location="商店"
    )

    chapter3_1 = Chapter(situation=situation3, chapter_name="商品結帳", sequence_number=1)
    sentences3_1 = [
        Sentence(chapter=chapter3_1, sentence_name="結帳", speaker_role=SpeakerRole.SELF, role_description="顧客", content="你好，我要結帳。"),
        Sentence(chapter=chapter3_1, sentence_name="掃描商品", speaker_role=SpeakerRole.OTHER, role_description="店員", content="好的，總共是350元。"),
    ]

    chapter3_2 = Chapter(situation=situation3, chapter_name="付款方式", sequence_number=2)
    sentences3_2 = [
        Sentence(chapter=chapter3_2, sentence_name="詢問付款方式", speaker_role=SpeakerRole.SELF, role_description="顧客", content="請問可以刷卡嗎？"),
        Sentence(chapter=chapter3_2, sentence_name="回覆付款方式", speaker_role=SpeakerRole.OTHER, role_description="店員", content="可以，這邊請。"),
        Sentence(chapter=chapter3_2, sentence_name="完成交易", speaker_role=SpeakerRole.OTHER, role_description="店員", content="這是您的發票，謝謝光臨。"),
    ]

    return {
        "situations": [situation1, situation2, situation3],
        "chapters": [chapter1_1, chapter1_2, chapter2_1, chapter2_2, chapter2_3, chapter3_1, chapter3_2],
        "sentences": sentences1_1 + sentences1_2 + sentences2_1 + sentences2_2 + sentences2_3 + sentences3_1 + sentences3_2
    }


def main():
    """Main function to create engine, tables, and session."""
    settings = get_settings()
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL, echo=True)

    # Create tables if they don't exist
    SQLModel.metadata.create_all(engine)

    from sqlmodel import Session
    
    data = create_seed_data()

    with Session(engine) as session:
        # You might want to clear existing data first
        # session.query(Sentence).delete()
        # session.query(Chapter).delete()
        # session.query(Situation).delete()
        
        for situation in data["situations"]:
            session.add(situation)
        
        # Chapters and Sentences are linked to situations and will be added via relationship
        # If you add them directly, ensure the relationships are correctly handled
        # For this structure, adding situations is enough due to cascading.

        session.commit()

    print("Seed data has been successfully added to the database.")


if __name__ == "__main__":
    main()


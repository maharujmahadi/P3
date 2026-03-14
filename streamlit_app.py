"""Streamlit web app for building vulnerability scoring and retrofit cost estimation."""

from __future__ import annotations

import os

import streamlit as st

from agent import run_building_consultant
from tools import calculate_vulnerability_score, estimate_retrofit_cost


def _load_env():
    # Load environment variables from .env if present.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass


def _format_currency(value: float) -> str:
    return f"{value:,.0f} Tk"


# Language dictionaries
TEXTS = {
    "title": {
        "en": "Dhaka Building Retrofit Consultant",
        "bn": "ঢাকা ভবন রেট্রোফিট পরামর্শক"
    },
    "description": {
        "en": "This tool uses deterministic scoring (based on the provided research tables) and an LLM agent to recommend retrofit methods and cost estimates.",
        "bn": "এই টুলটি নির্ধারিত স্কোরিং (প্রদত্ত গবেষণা টেবিলের ভিত্তিতে) এবং একটি LLM এজেন্ট ব্যবহার করে রেট্রোফিট পদ্ধতি এবং খরচ অনুমান সুপারিশ করে।"
    },
    "mode_manual": {
        "en": "Manual Calculator",
        "bn": "ম্যানুয়াল ক্যালকুলেটর"
    },
    "mode_agent": {
        "en": "Agent Chat",
        "bn": "এজেন্ট চ্যাট"
    },
    "manual_header": {
        "en": "Manual Calculator",
        "bn": "ম্যানুয়াল ক্যালকুলেটর"
    },
    "soil_zone": {
        "en": "Soil Zone",
        "bn": "মাটির জোন"
    },
    "construction_year": {
        "en": "Construction Year",
        "bn": "নির্মাণ বছর"
    },
    "soft_story": {
        "en": "Soft Story Condition",
        "bn": "সফ্ট স্টোরি অবস্থা"
    },
    "structure_type": {
        "en": "Structure Type",
        "bn": "স্ট্রাকচার টাইপ"
    },
    "num_floors": {
        "en": "Number of Floors",
        "bn": "তলার সংখ্যা"
    },
    "retrofit_intervention": {
        "en": "Retrofit Intervention",
        "bn": "রেট্রোফিট হস্তক্ষেপ"
    },
    "quantity": {
        "en": "Quantity",
        "bn": "পরিমাণ"
    },
    "compute_button": {
        "en": "Compute Vulnerability + Cost",
        "bn": "ভালনারেবিলিটি + খরচ গণনা করুন"
    },
    "vulnerability_score": {
        "en": "Vulnerability Score",
        "bn": "ভালনারেবিলিটি স্কোর"
    },
    "risk_tier": {
        "en": "Risk Tier",
        "bn": "ঝুঁকি স্তর"
    },
    "total_score": {
        "en": "Total Score",
        "bn": "মোট স্কোর"
    },
    "retrofit_cost_estimate": {
        "en": "Retrofit Cost Estimate",
        "bn": "রেট্রোফিট খরচ অনুমান"
    },
    "intervention": {
        "en": "Intervention",
        "bn": "হস্তক্ষেপ"
    },
    "estimated_cost": {
        "en": "Estimated cost",
        "bn": "অনুমানিত খরচ"
    },
    "cost_details": {
        "en": "Cost details",
        "bn": "খরচের বিস্তারিত"
    },
    "agent_header": {
        "en": "Agent-based Consultant",
        "bn": "এজেন্ট-ভিত্তিক পরামর্শক"
    },
    "agent_description": {
        "en": "Describe your building (e.g., 'I have a 5-story building in Mirpur built in 1995 with open ground floor parking'). The agent will extract parameters, compute a vulnerability score, and provide a retrofit cost estimate.",
        "bn": "আপনার ভবন বর্ণনা করুন (উদাহরণ: 'আমার মিরপুরে ১৯৯৫ সালে নির্মিত ৫ তলা ভবন রয়েছে যার গ্রাউন্ড ফ্লোর পার্কিং খোলা')। এজেন্ট প্যারামিটার বের করবে, ভালনারেবিলিটি স্কোর গণনা করবে এবং রেট্রোফিট খরচ অনুমান প্রদান করবে।"
    },
    "building_description": {
        "en": "Building description",
        "bn": "ভবনের বর্ণনা"
    },
    "run_agent": {
        "en": "Run Agent",
        "bn": "এজেন্ট চালান"
    },
    "error_empty_prompt": {
        "en": "Please describe your building so the agent can work.",
        "bn": "এজেন্ট কাজ করার জন্য আপনার ভবন বর্ণনা করুন।"
    },
    "consulting_agent": {
        "en": "Consulting the agent...",
        "bn": "এজেন্টের সাথে পরামর্শ করা হচ্ছে..."
    },
    "agent_failed": {
        "en": "Agent failed",
        "bn": "এজেন্ট ব্যর্থ হয়েছে"
    },
    "disclaimer": {
        "en": "Disclaimer: This tool utilizes Artificial Intelligence (AI) to generate responses and risk assessments based on the provided simulation scenarios. AI can occasionally produce incorrect or unverified information. The results should be used for educational and awareness purposes only and do not constitute professional engineering or legal advice. Always consult with a qualified structural engineer for specific building safety assessments.",
        "bn": "দাবিত্যাগ: এই টুলটি প্রদত্ত সিমুলেশন পরিস্থিতির ভিত্তিতে প্রতিক্রিয়া এবং ঝুঁকি মূল্যায়ন তৈরি করতে কৃত্রিম বুদ্ধিমত্তা (AI) ব্যবহার করে। AI কখনও কখনও ভুল বা অসত্য তথ্য তৈরি করতে পারে। ফলাফলগুলি শুধুমাত্র শিক্ষামূলক এবং সচেতনতা উদ্দেশ্যে ব্যবহার করা উচিত এবং এগুলি পেশাদার প্রকৌশল বা আইনি পরামর্শ গঠন করে না। নির্দিষ্ট ভবন নিরাপত্তা মূল্যায়নের জন্য সর্বদা একজন যোগ্য স্ট্রাকচারাল ইঞ্জিনিয়ারের সাথে পরামর্শ করুন।"
    },
    "language": {
        "en": "Language",
        "bn": "ভাষা"
    },
    "english": {
        "en": "English",
        "bn": "ইংরেজি"
    },
    "bangla": {
        "en": "Bangla",
        "bn": "বাংলা"
    }
}


def get_text(key: str, lang: str) -> str:
    return TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("en", key))


def _run_manual_ui(lang: str) -> None:
    st.header(get_text("manual_header", lang))

    # Zone options with detailed descriptions from research
    zone_options = {
        "Zone 1 (Pleistocene Terrace) - Locations: Mirpur, Tejgaon, Dhanmondi, Cantonment, Old Dhaka (core areas), Ramna, Shahbagh, Lalmatia - Site Class D (Stiff Soil)": "Zone 1",
        "Zone 2 (Holocene Alluvial Valley Fill and Holocene Terrace) - Locations: Mohammadpur, Rampura, Malibagh, Shahjahanpur, Khilgaon, parts of Mirpur (fringes), Keraniganj (near river), Jatrabari (portions) - Site Class D to E (Stiff to Soft Soil transition)": "Zone 2",
        "Zone 3 (Artificial Fill and Holocene Alluvium) - Locations: Basundhara, Purbachal, Uttara (3rd phase), Mohammadpur (low-lying areas), Rampura (eastern parts), Jatrabari (low areas), Demra, Postogola, Jurain, parts of Keraniganj, Badda (portions) - Site Class E (Soft Soil)": "Zone 3",
    }

    col1, col2 = st.columns(2)
    with col1:
        selected_zone_display = st.selectbox(get_text("soil_zone", lang), list(zone_options.keys()), index=1)
        zone = zone_options[selected_zone_display]
        construction_year = st.number_input(get_text("construction_year", lang), min_value=1900, max_value=2040, value=1995)
        soft_story = st.selectbox(
            get_text("soft_story", lang), ["Open/Piloti ground floor", "Solid ground floor"], index=0
        )
        structure_type = st.selectbox(
            get_text("structure_type", lang),
            [
                "URM (Old Dhaka)",
                "RC Soft Story (6-9 story)",
                "RC Infilled (Engineered)",
                "RC Non-Engineered (Poor Detailing)",
                "High-Rise (Deep Pile)",
            ],
        )

    with col2:
        num_floors = st.number_input(get_text("num_floors", lang), min_value=1, max_value=20, value=1)

        # Dynamic intervention options based on selected zone (from Excel Cost Table)
        intervention_options = {
            "Zone 1": [
                "Column Jacketing (with footing)",
                "Shear Walls (with footing)",
                "Steel bracing work in-fill steel brace",
            ],
            "Zone 2": [
                "Column Jacketing (with footing)",
                "Shear Walls (with footing)",
                "Steel bracing work in-fill steel brace",
                "Deep foundation retrofitting",
            ],
            "Zone 3": [
                "Shear Walls (with footing)",
                "Deep foundation piles",
                "Soil stabilization",
            ],
        }
        intervention = st.selectbox(
            get_text("retrofit_intervention", lang),
            intervention_options.get(zone, ["Shear Walls (with footing)"]),
        )

        unit_labels = {
            "Column Jacketing (with footing)": "meters of column",
            "Shear Walls (with footing)": "sqm of shear wall",
            "Steel bracing work in-fill steel brace": "sqm of frame",
            "Deep foundation retrofitting": "(consult engineer)",
            "Deep foundation piles": "(consult engineer)",
            "Soil stabilization": "(consult engineer)",
        }
        unit_label = unit_labels.get(intervention, "unit")

        quantity = st.number_input(
            f"{get_text('quantity', lang)} ({unit_label})",
            min_value=0.0,
            value=100.0 if "sqm" in unit_label or "meters" in unit_label else 0.0,
        )

    if st.button(get_text("compute_button", lang)):
        vuln = calculate_vulnerability_score(zone, int(construction_year), soft_story, structure_type)
        cost = estimate_retrofit_cost(intervention, float(quantity), zone=zone, num_floors=int(num_floors))

        st.subheader(get_text("vulnerability_score", lang))
        st.write(
            f"**{get_text('risk_tier', lang)}:** {vuln.risk_tier} "
            f"**{get_text('total_score', lang)}:** {vuln.total_score}"  # noqa: E501
            f"(Zone: {vuln.zone_points} pts, Year: {vuln.year_points} pts, Soft story: {vuln.soft_story_points} pts, Structure: {vuln.structure_points} pts)"
        )

        st.subheader(get_text("retrofit_cost_estimate", lang))
        st.write(f"**{get_text('intervention', lang)}:** {cost.intervention_type}")
        st.write(f"**{get_text('quantity', lang)}:** {cost.quantity:,.1f} {cost.unit}")
        st.write(f"**{get_text('estimated_cost', lang)}:** {_format_currency(cost.estimated_cost_tk)}")
        st.write(f"**{get_text('cost_details', lang)}:**")
        st.write(cost.details)

    # Disclaimer
    st.info(get_text("disclaimer", lang))


def _run_agent_ui(lang: str) -> None:
    st.header(get_text("agent_header", lang))
    st.write(get_text("agent_description", lang))
    user_prompt = st.text_area(get_text("building_description", lang), height=150)

    if st.button(get_text("run_agent", lang)):
        if not user_prompt.strip():
            st.error(get_text("error_empty_prompt", lang))
        else:
            with st.spinner(get_text("consulting_agent", lang)):
                try:
                    report = run_building_consultant(user_prompt)
                    st.markdown(report)
                except Exception as e:
                    st.error(f"{get_text('agent_failed', lang)}: {e}")

    # Disclaimer
    st.info(get_text("disclaimer", lang))


def main() -> None:
    _load_env()

    st.set_page_config(
        page_title="Dhaka Building Retrofit Consultant",
        page_icon="🏗️",
        layout="wide",
    )

    # Language selector
    lang_options = {"English": "en", "বাংলা": "bn"}
    selected_lang_display = st.sidebar.selectbox(get_text("language", "en"), list(lang_options.keys()), index=0)
    lang = lang_options[selected_lang_display]

    st.title(get_text("title", lang))
    st.write(get_text("description", lang))

    mode_options = [get_text("mode_manual", lang), get_text("mode_agent", lang)]
    mode = st.sidebar.radio(get_text("mode_manual", lang) if lang == "en" else "Mode", mode_options)

    if mode == get_text("mode_manual", lang):
        _run_manual_ui(lang)
    else:
        _run_agent_ui(lang)


if __name__ == "__main__":
    main()

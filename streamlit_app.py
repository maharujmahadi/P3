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


def _run_manual_ui(language: str) -> None:
    st.header("Manual Calculator" if language == "English" else "ম্যানুয়াল ক্যালকুলেটর")

    # Zone options with detailed descriptions from research
    zone_options = {
        "Zone 1 (Pleistocene Terrace) - Locations: Mirpur, Tejgaon, Dhanmondi, Cantonment, Old Dhaka (core areas), Ramna, Shahbagh, Lalmatia - Site Class D (Stiff Soil)": "Zone 1",
        "Zone 2 (Holocene Alluvial Valley Fill and Holocene Terrace) - Locations: Mohammadpur, Rampura, Malibagh, Shahjahanpur, Khilgaon, parts of Mirpur (fringes), Keraniganj (near river), Jatrabari (portions) - Site Class D to E (Stiff to Soft Soil transition)": "Zone 2",
        "Zone 3 (Artificial Fill and Holocene Alluvium) - Locations: Basundhara, Purbachal, Uttara (3rd phase), Mohammadpur (low-lying areas), Rampura (eastern parts), Jatrabari (low areas), Demra, Postogola, Jurain, parts of Keraniganj, Badda (portions) - Site Class E (Soft Soil)": "Zone 3",
    }

    col1, col2 = st.columns(2)
    with col1:
        selected_zone_display = st.selectbox("Soil Zone" if language == "English" else "মাটি জোন", list(zone_options.keys()), index=1)
        zone = zone_options[selected_zone_display]
        construction_year = st.number_input("Construction Year" if language == "English" else "নির্মাণ বছর", min_value=1900, max_value=2040, value=1995)
        soft_story = st.selectbox(
            "Soft Story Condition" if language == "English" else "সফ্ট স্টোরি অবস্থা",
            ["Open/Piloti ground floor", "Solid ground floor"] if language == "English" else ["খোলা/পিলোটি গ্রাউন্ড ফ্লোর", "সলিড গ্রাউন্ড ফ্লোর"],
            index=0
        )
        structure_type = st.selectbox(
            "Structure Type" if language == "English" else "স্ট্রাকচার টাইপ",
            [
                "URM (Old Dhaka)",
                "RC Soft Story (6-9 story)",
                "RC Infilled (Engineered)",
                "RC Non-Engineered (Poor Detailing)",
                "High-Rise (Deep Pile)",
            ] if language == "English" else [
                "URM (পুরানো ঢাকা)",
                "RC সফ্ট স্টোরি (6-9 তলা)",
                "RC ইনফিল্ড (ইঞ্জিনিয়ার্ড)",
                "RC নন-ইঞ্জিনিয়ার্ড (খারাপ ডিটেলিং)",
                "হাই-রাইজ (ডিপ পাইল)",
            ],
        )

    with col2:
        num_floors = st.number_input("Number of Floors" if language == "English" else "তলার সংখ্যা", min_value=1, max_value=20, value=1)

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
            "Retrofit Intervention" if language == "English" else "রেট্রোফিট হস্তক্ষেপ",
            intervention_options.get(zone, ["Shear Walls (with footing)"]),
        )

        unit_labels = {
            "Column Jacketing (with footing)": "meters of column" if language == "English" else "কলামের মিটার",
            "Shear Walls (with footing)": "sqm of shear wall" if language == "English" else "শিয়ার ওয়ালের বর্গমিটার",
            "Steel bracing work in-fill steel brace": "sqm of frame" if language == "English" else "ফ্রেমের বর্গমিটার",
            "Deep foundation retrofitting": "(consult engineer)" if language == "English" else "(ইঞ্জিনিয়ারের সাথে পরামর্শ করুন)",
            "Deep foundation piles": "(consult engineer)" if language == "English" else "(ইঞ্জিনিয়ারের সাথে পরামর্শ করুন)",
            "Soil stabilization": "(consult engineer)" if language == "English" else "(ইঞ্জিনিয়ারের সাথে পরামর্শ করুন)",
        }
        unit_label = unit_labels.get(intervention, "unit")

        quantity = st.number_input(
            f"Quantity ({unit_label})" if language == "English" else f"পরিমাণ ({unit_label})",
            min_value=0.0,
            value=100.0 if "sqm" in unit_label or "meters" in unit_label else 0.0,
        )

    if st.button("Compute Vulnerability + Cost" if language == "English" else "ঝুঁকি + খরচ গণনা করুন"):
        vuln = calculate_vulnerability_score(zone, int(construction_year), soft_story, structure_type)
        cost = estimate_retrofit_cost(intervention, float(quantity), zone=zone, num_floors=int(num_floors))

        st.subheader("Vulnerability Score" if language == "English" else "ঝুঁকি স্কোর")
        st.write(
            f"**Risk Tier:** {vuln.risk_tier} "
            f"**Total Score:** {vuln.total_score}"  # noqa: E501
            f"(Zone: {vuln.zone_points} pts, Year: {vuln.year_points} pts, Soft story: {vuln.soft_story_points} pts, Structure: {vuln.structure_points} pts)"
        )

        st.subheader("Retrofit Cost Estimate" if language == "English" else "রেট্রোফিট খরচ অনুমান")
        st.write(f"**Intervention:** {cost.intervention_type}")
        st.write(f"**Quantity:** {cost.quantity:,.1f} {cost.unit}")
        st.write(f"**Estimated cost:** {_format_currency(cost.estimated_cost_tk)}")
        st.write("**Cost details:**")
        st.write(cost.details)

    # Disclaimer
    disclaimer_en = "Disclaimer: This tool utilizes Artificial Intelligence (AI) to generate responses and risk assessments based on the provided simulation scenarios. AI can occasionally produce incorrect or unverified information. The results should be used for educational and awareness purposes only and do not constitute professional engineering or legal advice. Always consult with a qualified structural engineer for specific building safety assessments."
    disclaimer_bn = "দাবিত্যাগ: এই টুলটি প্রদত্ত সিমুলেশন পরিস্থিতি ভিত্তিতে প্রতিক্রিয়া এবং ঝুঁকি মূল্যায়ন তৈরি করতে কৃত্রিম বুদ্ধিমত্তা (AI) ব্যবহার করে। AI কখনও কখনও ভুল বা অসত্য তথ্য তৈরি করতে পারে। ফলাফলগুলি শুধুমাত্র শিক্ষামূলক এবং সচেতনতা উদ্দেশ্যে ব্যবহার করা উচিত এবং এগুলি পেশাদার প্রকৌশল বা আইনি পরামর্শ গঠন করে না। নির্দিষ্ট ভবন নিরাপত্তা মূল্যায়নের জন্য সর্বদা একজন যোগ্য স্ট্রাকচারাল ইঞ্জিনিয়ারের সাথে পরামর্শ করুন।"
    st.info(disclaimer_en if language == "English" else disclaimer_bn)


def _run_agent_ui(language: str) -> None:
    st.header("Agent-based Consultant" if language == "English" else "এজেন্ট-ভিত্তিক পরামর্শক")
    st.write(
        "Describe your building (e.g., 'I have a 5-story building in Mirpur built in 1995 with open ground floor parking'). The agent will extract parameters, compute a vulnerability score, and provide a retrofit cost estimate." if language == "English" else "আপনার ভবন বর্ণনা করুন (যেমন, 'আমার কাছে মিরপুরে 1995 সালে নির্মিত 5-তলা ভবন রয়েছে যার খোলা গ্রাউন্ড ফ্লোর পার্কিং রয়েছে')। এজেন্ট প্যারামিটারগুলি বের করবে, একটি ঝুঁকি স্কোর গণনা করবে এবং একটি রেট্রোফিট খরচ অনুমান প্রদান করবে।"
    )
    user_prompt = st.text_area("Building description" if language == "English" else "ভবনের বর্ণনা", height=150)

    if st.button("Run Agent" if language == "English" else "এজেন্ট চালান"):
        if not user_prompt.strip():
            st.error("Please describe your building so the agent can work." if language == "English" else "এজেন্ট কাজ করার জন্য আপনার ভবন বর্ণনা করুন।")
        else:
            with st.spinner("Consulting the agent..." if language == "English" else "এজেন্টের সাথে পরামর্শ করা হচ্ছে..."):
                try:
                    report = run_building_consultant(user_prompt)
                    st.markdown(report)
                except Exception as e:
                    st.error(f"Agent failed: {e}")

    # Disclaimer
    disclaimer_en = "Disclaimer: This tool utilizes Artificial Intelligence (AI) to generate responses and risk assessments based on the provided simulation scenarios. AI can occasionally produce incorrect or unverified information. The results should be used for educational and awareness purposes only and do not constitute professional engineering or legal advice. Always consult with a qualified structural engineer for specific building safety assessments."
    disclaimer_bn = "দাবিত্যাগ: এই টুলটি প্রদত্ত সিমুলেশন পরিস্থিতি ভিত্তিতে প্রতিক্রিয়া এবং ঝুঁকি মূল্যায়ন তৈরি করতে কৃত্রিম বুদ্ধিমত্তা (AI) ব্যবহার করে। AI কখনও কখনও ভুল বা অসত্য তথ্য তৈরি করতে পারে। ফলাফলগুলি শুধুমাত্র শিক্ষামূলক এবং সচেতনতা উদ্দেশ্যে ব্যবহার করা উচিত এবং এগুলি পেশাদার প্রকৌশল বা আইনি পরামর্শ গঠন করে না। নির্দিষ্ট ভবন নিরাপত্তা মূল্যায়নের জন্য সর্বদা একজন যোগ্য স্ট্রাকচারাল ইঞ্জিনিয়ারের সাথে পরামর্শ করুন।"
    st.info(disclaimer_en if language == "English" else disclaimer_bn)


def main() -> None:
    _load_env()

    st.set_page_config(
        page_title="Dhaka Building Retrofit Consultant",
        page_icon="🏗️",
        layout="wide",
    )

    # Language selector
    language = st.sidebar.radio("Language / ভাষা", ["English", "বাংলা"], index=0)

    st.title("Dhaka Building Retrofit Consultant" if language == "English" else "ঢাকা ভবন রেট্রোফিট পরামর্শক")
    st.write(
        "This tool uses deterministic scoring (based on the provided research tables) and an LLM agent to recommend retrofit methods and cost estimates." if language == "English" else "এই টুলটি নির্ধারিত স্কোরিং (প্রদত্ত গবেষণা টেবিল ভিত্তিতে) এবং একটি LLM এজেন্ট ব্যবহার করে রেট্রোফিট পদ্ধতি এবং খরচ অনুমান সুপারিশ করে।"
    )

    mode = st.sidebar.radio(
        "Mode" if language == "English" else "মোড",
        ["Manual Calculator", "Agent Chat"] if language == "English" else ["ম্যানুয়াল ক্যালকুলেটর", "এজেন্ট চ্যাট"]
    )

    if mode == "Manual Calculator" or mode == "ম্যানুয়াল ক্যালকুলেটর":
        _run_manual_ui(language)
    else:
        _run_agent_ui(language)


if __name__ == "__main__":
    main()

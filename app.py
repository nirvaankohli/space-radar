import flask
from flask import Flask, jsonify, request, render_template
import data_pipeline
import os
import json
from datetime import datetime

app = Flask(__name__)


def load_stories():
    try:
        with open("data/db/stories.json", "r", encoding="utf-8") as f:
            stories = json.load(f)

        cleaned_stories = []
        for story in stories:

            cleaned_story = {
                "rep_title": story.get("rep_title", "Untitled"),
                "sources": story.get("sources", ["Unknown"]),
                "timestamp": story.get("timestamp", ""),
                "summary": story.get("summary", ""),
                "rep_text": story.get("rep_text", ""),
                "because": story.get("because", ""),
                "topics": story.get("topics", []),
                "urls": story.get("urls", []),
                "score": story.get("score", 0.0),
                "score_components": story.get("score_components", {"llm_score": 0.0}),
            }

            if not cleaned_story["summary"] and cleaned_story["rep_text"]:

                text = cleaned_story["rep_text"][:400]
                last_period = text.rfind(".")
                if last_period > 200:
                    cleaned_story["summary"] = text[: last_period + 1]
                else:
                    cleaned_story["summary"] = text[:300] + "..."

            cleaned_stories.append(cleaned_story)

        # Sort by score
        cleaned_stories.sort(
            key=lambda x: -x.get("score_components", {}).get(
                "llm_score", x.get("score", 0)
            ),
            reverse=False,
        )

        return cleaned_stories[:25]  # Show 25 stories instead of 10

    except FileNotFoundError:
        print("Story candidates file not found")
        return []

    except Exception as e:
        print(f"Error loading stories: {e}")
        return []


def get_trending_topics():
    try:
        stories = load_stories()
        all_topics = []

        for story in stories:
            topics = story.get("topics", [])
            for topic in topics:
                if topic and topic.strip():
                    # Clean and format topic names
                    clean_topic = topic.replace("_", " ").title().strip()
                    if clean_topic and clean_topic not in all_topics:
                        all_topics.append(clean_topic)

        default_topics = [
            "Mars Exploration",
            "Satellite Technology",
            "Space Policy",
            "Astronaut Missions",
            "Scientific Discovery",
            "Skywatching",
            "SpaceX",
            "NASA Missions",
            "International Space Station",
            "Planetary Science",
            "Space Weather",
            "Rocket Technology",
        ]

        combined_topics = all_topics + [
            t for t in default_topics if t not in all_topics
        ]

        return (
            combined_topics[:12] if len(combined_topics) >= 12 else combined_topics * 2
        )

    except Exception as e:
        print(f"Error getting trending topics: {e}")
        return [
            "Mars Exploration",
            "Satellite Technology",
            "Space Policy",
            "Astronaut Missions",
            "Scientific Discovery",
            "Skywatching",
        ] * 2


@app.route("/")
def index():

    stories = load_stories()
    trending_topics = get_trending_topics()
    return render_template(
        "index.html", stories=stories, trending_topics=trending_topics
    )


@app.route("/api/stories")
def api_stories():

    stories = load_stories()
    return jsonify(stories)


@app.route("/run_pipeline", methods=["POST"])
def run_pipeline():

    result = data_pipeline.run_pipeline()
    return jsonify({"status": "completed", "result": result})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)

import llm
from pathlib import Path
import json
from datetime import datetime, timezone
import math


DB_DIR = Path(__file__).parent.parent.parent / "data" / "db"
CAN_FILE = DB_DIR / "story_candidates.json"
STORY_FILE = DB_DIR / "stories.json"


class LLMProcessor:

    def __init__(self, api_key="use_local"):

        self.client = llm.LLMClient(api_key)
        self.db_dir = DB_DIR
        self.can_file = CAN_FILE
        self.story_file = STORY_FILE
        self.weights = {"llms": 0.6, "reliability": 0.2, "recency": 0.2}
        self.reliability_scores = {
            "NASA": 0.99,
            "NASA Blogs": 0.96,
            "JPL": 0.99,
            "ESA": 0.99,
            "ESA Webb": 0.98,
            "SpaceNews": 0.92,
            "Spaceflight Now": 0.9,
            "NOAA NESDIS": 0.99,
            "Nature Astronomy": 0.97,
            "arXiv astro-ph.EP": 0.9,
            "arXiv astro-ph.IM": 0.9,
            "arXiv astro-ph.GA": 0.9,
            "Planetary Society": 0.93,
            "SpaceX Updates": 0.95,
            "CNSA Watch": 0.85,
        }

    def load_candidates(self, return_type="none"):

        if not self.can_file.exists():

            raise FileNotFoundError(f"Candidate file not found: {self.can_file}")

        with open(self.can_file, "r", encoding="utf-8") as f:

            self.candidates = json.load(f)

        if return_type != "none":

            return self.candidates

    def avg(self, lst):

        return sum(lst) / len(lst) if lst else 0.0

    def load_stories(self):

        if not self.story_file.exists():

            return []

        with open(self.story_file, "r", encoding="utf-8") as f:

            self.stories = json.load(f)

        return self.stories

    def process_candidates(self):

        existing_stories = self.load_stories()
        existing_cluster_ids = {
            story.get("cluster_id", ""): story for story in existing_stories
        }

        processed_stories = []
        story = {}
        self.load_candidates()

        new_candidates = [
            candidate
            for candidate in self.candidates
            if candidate.get("cluster_id", "") not in existing_cluster_ids
        ]

        existing_candidates = [
            candidate
            for candidate in self.candidates
            if candidate.get("cluster_id", "") in existing_cluster_ids
        ]

        length_of_candidates = len(new_candidates)
        existing_count = len(existing_candidates)
        total_candidates = len(self.candidates)

        print(f"Total story candidates: {total_candidates}")
        print(f"Already processed (updating recency): {existing_count}")
        print(f"New candidates to process: {length_of_candidates}")

        for candidate in existing_candidates:
            cluster_id = candidate.get("cluster_id", "")
            existing_story = existing_cluster_ids[cluster_id]

            new_recency_score = self.calculate_recency_score(candidate)

            existing_story["score_components"]["recency_score"] = new_recency_score

            existing_story["score"] = (
                self.weights["llms"] * existing_story["score_components"]["llm_score"]
                + self.weights["reliability"]
                * existing_story["score_components"]["reliability_score"]
                + self.weights["recency"] * new_recency_score
            )

            processed_stories.append(existing_story)

        count = 0
        successful_count = 0
        failed_count = 0

        for candidate in new_candidates:

            count += 1

            cluster_id = candidate.get("cluster_id", "")
            print(
                f"Processing NEW candidate cluster ID: {cluster_id} ({count}/{length_of_candidates})"
            )

            # Initialize default values
            response = {"score": {"score": 0.0, "reasoning": "Default"}}
            story = candidate.copy()

            try:
                r = self.client.request(candidate)
                response_content = r["choices"][0]["message"]["content"]
                response = json.loads(response_content)

                story["because"] = response.get("because", "")
                story["summary"] = response.get("summary", "")
                story["topics"] = response.get("topics", [])
                story["reasoning"] = response.get("score", {}).get("reasoning", "")

                successful_count += 1
                print(f"✓ Successfully processed cluster {cluster_id}")

            except (json.JSONDecodeError, KeyError, Exception) as e:
                failed_count += 1
                print(f"✗ Error processing cluster {cluster_id}: {e}")
                print(f"Raw response: {r if 'r' in locals() else 'No response'}")

                story["because"] = "Error processing with LLM"
                story["summary"] = f"Processing failed: {str(e)}"
                story["topics"] = ["error"]
                story["reasoning"] = "LLM processing failed"

                # Reset response to default for failed cases
                response = {"score": {"score": 0.0, "reasoning": "Processing failed"}}

            recency_score = self.calculate_recency_score(candidate)
            reliability_score = self.avg(
                [
                    self.reliability_scores.get(source, 0.5)
                    for source in candidate.get("sources", [])
                ]
            )

            story["score_components"] = {
                "llm_score": response.get("score", {}).get("score", 0.0),
                "reliability_score": reliability_score,
                "recency_score": recency_score,
            }

            story["score"] = (
                self.weights["llms"] * response.get("score", {}).get("score", 0.0)
                + self.weights["reliability"] * reliability_score
                + self.weights["recency"] * recency_score
            )

            processed_stories.append(story)

            # Add small delay between requests to be API-friendly
            if count < length_of_candidates:  # Don't delay after last item
                import time

                time.sleep(1)  # 1 second delay between requests

        self.processed_stories = processed_stories

        with open(self.story_file, "w", encoding="utf-8") as f:

            json.dump(self.processed_stories, f, indent=4, ensure_ascii=False)

        print(f"\nProcessing Summary:")
        print(f"✓ Successfully processed: {successful_count}")
        print(f"✗ Failed to process: {failed_count}")
        print(f"📊 Total stories saved: {len(self.processed_stories)}")

    def calculate_recency_score(self, candidate):

        ts_str = candidate.get("timestamp", "")

        now = datetime.now(timezone.utc)
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
        hours = (now - ts).total_seconds() / 3600.0
        if hours < 0:
            hours = 0
        return math.exp(-hours / 48.0)


if __name__ == "__main__":
    print("Starting LLM processing of story candidates...")
    processor = LLMProcessor(api_key="use_local")
    processor.process_candidates()
    print("LLM processing completed. Stories saved to:", processor.story_file)

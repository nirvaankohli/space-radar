# Plan For Agents

# The Goals

* Build a **multi-agent pipeline** that turns those(the db) articales into:
  * A list of **stories**(clusters of related articales)
  * Each with a:
    * summary
    * a "because" line
    * a score
  * Stored in a stories JSON file that the UI can read

# Data Layout

* Articale schema 
  * id, url, source, ts, title, text
* Cluster schema:
  * cluster_id, member_ids[], rep_id.
* Story schema (final output):
  * story_id, headline, summary, because, score, ts, source, topics[], member_ids[]

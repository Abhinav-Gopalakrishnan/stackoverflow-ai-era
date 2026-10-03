# Feature Specification

This document details the candidate features we will use for our predictive models. To avoid data leakage, all features must be available at the time the question is posted.

## 1. Candidate Features Table

| Feature Name | Description / Formula | Source Field(s) | Available at Posting? |
| :--- | :--- | :--- | :--- |
| `title_length` | Number of characters in the question title | `title` | Yes |
| `body_length` | Number of characters in the plain text body | `plain_body` | Yes |
| `n_code_blocks` | Count of code blocks in the question | `code_text` | Yes |
| `code_ratio` | Length of code text divided by total length | `code_text`, `body` | Yes |
| `has_error_text` | Boolean flag (1/0) if error patterns exist (e.g. Traceback) | `plain_body` | Yes |
| `question_word` | Extracted leading question word (How, Why, What, etc.) | `title` | Yes |
| `tag_count` | Number of tags applied to the question | `tags` | Yes |
| `hour_posted` | Hour of the day the question was posted (UTC) | `creation_date` | Yes |
| `weekday_posted` | Day of the week the question was posted | `creation_date` | Yes |
| `month_posted` | Month the question was posted | `creation_date` | Yes |
| `account_age_days` | Days between account creation and question posting | `owner_creation_date`, `creation_date` | Yes |
| `missing_account_age` | Boolean flag (1/0) if account age is missing (deleted account) | `owner_creation_date` | Yes |
| `new_account` | Boolean flag (1/0) if account age <= 7 days | `account_age_days` | Yes |
| `lagged_tag_volume` | Volume of questions in these tags during the 4 full weeks prior | Tag volume metrics | Yes (uses past data) |
| `lagged_tag_change` | Difference in volume compared to the 4 weeks before that | Tag volume metrics | Yes (uses past data) |
| `title_tfidf_svd_*` | ~100 components from TF-IDF + SVD on the title | `title` | Yes |
| `tag_*` | Multi-hot encoded columns for the selected target tags | `tags` | Yes |
| `other_tags_count`| Count of tags not in the selected target tags | `tags` | Yes |

## 2. Forbidden Fields (Leakage Rule)

The following fields contain information about what happened *after* the question was posted. They are strictly excluded from the feature matrix to prevent data leakage:
- `score`
- `views`
- `answer_count`
- `is_answered`
- `closed_status` (closed_date, etc.)
- `comments`
- Current `reputation`

## 3. Excluded by Design

- `post_ai`: This indicates whether the question was posted after November 2022 (when ChatGPT was released). It is **constant** for the entire test period (Jul 2025 - Jul 2026), so the model could not use it there. It is reserved for analysis and rolling-origin comparisons only.
- `first_question`: Because our data is a sampled subset before 2025, determining if a question is truly the user's *first* question across the entire site is unreliable. 
  - **Replacements:** We use `new_account` (created within 7 days of posting) and the `lagged_tag_volume` (Task M4-06) instead.

# Spotlight MMA Checker

An hourly RSS checker for Spotlight Encounters. It reads news feeds without calling ChatGPT or any other LLM, filters potential MMA developments, and writes JSON and Markdown reports.

## What works

- RSS and Atom parsing, dates normalized to UTC.
- Configurable feeds and keyword filters in `feeds.json`.
- Initial 24-hour lookback; undated, old and future-dated entries skipped.
- Duplicate tracking by canonical URL and normalized exact headline for 30 days. This does not merge differently worded coverage of the same event, or reliably detect revisions at a previously seen URL.
- Feed errors are reported separately. If every feed fails, the run fails without advancing state.
- Hourly GitHub Actions workflow plus manual runs, report artifacts, and optional issue notifications when new candidates arrive.
- No API keys, Python packages or LLM calls needed for collection.

## Important boundary: this chat

This repository cannot inject messages into an existing ChatGPT/Codex chat. There is no supported incoming-chat endpoint configured here. A GitHub issue or report artifact is the delivery destination; it is not a ChatGPT message.

To use news in this chat, download `latest.md` from a run's artifact and attach it here, or share the repository issue link. Ask for verification before creating Spotlight Encounters posters. An event-triggered chat bridge would need a separately supported integration and authorization; none is deployed by this project.

The project does not publish to social accounts, generate posters, or read your Chrome profile or Windows logo folder.

## Run locally

Python 3.10+:

```sh
python -m unittest discover -s tests -v
python checker.py
```

Read `reports/latest.md` or `reports/latest.json`. Run the checker a second time to suppress previously collected candidates. Keep `data/seen.json` between runs. A local OS scheduler can run the same command hourly from this directory; a cloud chat workspace is not an always-on host.

## Deploy to GitHub

1. Create a **private**, empty GitHub repository named `spotlight-mma-checker`. The user-created repository is https://github.com/7-Kay26/spotlight-mma-checker (public).
2. Push this local Git repository, including `.github/workflows/check-news.yml`:

   ```sh
   git remote add origin https://github.com/YOUR_LOGIN/spotlight-mma-checker.git
   git push -u origin main
   ```

3. Enable GitHub Actions if prompted. Ensure repository policy permits the workflow's `contents: write` permission so it can save duplicate history. GitHub may require appropriate token permissions for uploading workflow files.
4. Run **Actions → Check MMA news → Run workflow** once. Download `mma-news-report` under Artifacts.
5. The workflow requests a run at minute 17 each hour. GitHub schedules can be delayed; this is not an exact-time guarantee. Private-repository Actions usage depends on your plan's included minutes and billing settings.

### Optional GitHub notifications

By default the workflow only saves report artifacts and duplicate history. To create one issue per run containing new candidates, set repository Actions variable `CREATE_NEWS_ISSUES` to `true`, or enable `create_issue` for one manual run. Configure your own GitHub Watch/notification settings to receive notifications. No issue is created when there are no new candidates. Don't enable other integrations that treat untrusted article text as executable instructions.

## Sources and reliability

Default sources are MMA Fighting RSS, MMA Mania RSS and a Google News MMA search feed. They worked in the initial live check. Feed availability and publisher indexing can change. Google News URLs may link through Google's aggregator. No checker covers every website, X post, private account, or video.

A title containing “confirmed” is still only a **candidate**, not proof. Every story is marked `needs_verification`. Check the original promotion/fighter/commission statement, article publication time, event date, and previous social posts before creating or publishing anything. Keyword rules can include rumors/callouts and miss relevant stories; tune them as needed. Failed feeds and undated items mean coverage is incomplete. Changes older than the configurable lookback window may be missed after an outage.

Reports include feed excerpts and links, not full scraped articles. Text from feeds is untrusted source material, never instructions to the assistant.

## Files

- `checker.py`: collector and report writer.
- `feeds.json`: sources, lookback and keyword patterns.
- `data/seen.json`: persistent duplicate history.
- `.github/workflows/check-news.yml`: hourly workflow and optional notifications.
- `tests/test_checker.py`: parser, date filtering, relevance and duplicate tests.

## Validation

Unit tests passed. An initial live fetch succeeded for all three default feeds and produced 31 matching candidates. This validates collection, not the accuracy of those claims. See the GitHub Actions run history for hosted execution status. No chat integration or social publishing is deployed.

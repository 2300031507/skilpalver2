// ============================================================
//  RAW EVENTS  –  high-volume, append-only event log
// ============================================================
db.createCollection("raw_events", {
  timeseries: {                       // MongoDB 5.0+ time-series collection
    timeField: "timestamp",           // auto-bucketing by time
    metaField: "meta",                // compound {university_id, student_id, course_id}
    granularity: "minutes"
  }
});
// Compound index for per-student queries (still useful on time-series)
db.raw_events.createIndex({ "meta.university_id": 1, "meta.student_id": 1, timestamp: -1 });
// TTL – auto-delete raw events older than 180 days (adjustable)
db.raw_events.createIndex({ timestamp: 1 }, { expireAfterSeconds: 15552000 });
// Event-type lookups
db.raw_events.createIndex({ "meta.university_id": 1, event_type: 1, timestamp: -1 });

// ============================================================
//  STUDENT FEATURES  –  aggregated feature vectors
// ============================================================
db.createCollection("student_features");
db.student_features.createIndex(
  { university_id: 1, student_id: 1, course_id: 1 },
  { unique: true }
);
db.student_features.createIndex({ university_id: 1, "features.attendance_percent": 1 });

// ============================================================
//  PLATFORM CONFIG  –  university-level coding platform setup
//  Admin defines once → all students of that university see it
// ============================================================
db.createCollection("platform_configs");
db.platform_configs.createIndex({ university_id: 1 }, { unique: true });
// Example document:
// {
//   university_id: "UNI001",
//   platforms: [
//     { slug: "leetcode",   display_name: "LeetCode",   base_url: "https://leetcode.com",  profile_url_template: "https://leetcode.com/u/{username}", active: true },
//     { slug: "codechef",   display_name: "CodeChef",   base_url: "https://www.codechef.com", profile_url_template: "https://www.codechef.com/users/{username}", active: true },
//     { slug: "codeforces", display_name: "Codeforces", base_url: "https://codeforces.com", profile_url_template: "https://codeforces.com/profile/{username}", active: true }
//   ],
//   updated_at: ISODate(),
//   updated_by: "admin@uni.edu"
// }

// ============================================================
//  STUDENT PLATFORM PROFILES  –  student links their handles
// ============================================================
db.createCollection("student_platform_profiles");
db.student_platform_profiles.createIndex(
  { university_id: 1, student_id: 1 },
  { unique: true }
);
// Fast lookup when ingesting events by platform username
db.student_platform_profiles.createIndex(
  { university_id: 1, "profiles.platform_slug": 1, "profiles.username": 1 }
);
// Example document:
// {
//   university_id: "UNI001",
//   student_id: "S001",
//   profiles: [
//     { platform_slug: "leetcode",   username: "alice_lc",   linked_at: ISODate(), verified: true },
//     { platform_slug: "codechef",   username: "alice_cc",   linked_at: ISODate(), verified: false }
//   ]
// }

// ============================================================
//  BULK INGEST TRACKING  –  deduplicate & track batch uploads
// ============================================================
db.createCollection("bulk_ingest_jobs");
db.bulk_ingest_jobs.createIndex({ university_id: 1, status: 1 });
db.bulk_ingest_jobs.createIndex({ created_at: 1 }, { expireAfterSeconds: 2592000 }); // 30-day TTL


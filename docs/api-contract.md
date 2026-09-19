# Smart Attendance Verification - API Contract

## Base URL
`/api/v1`

---

## 1. Classroom Verification (AI Service Integration)
* **Endpoint:** `POST /attendance/verify`
* **Content-Type:** `multipart/form-data`
* **Request:**
  * `session_id` (string, required)
  * `frame_image` (file, binary, required)
* **Success Response (200 OK):**
  ```json
  {
    "status": "success",
    "data": {
      "session_id": "sess_102",
      "detected_faces_count": 28,
      "verified_students": [
        { "student_id": "std_2026_01", "confidence": 0.96, "timestamp": "2026-09-19T14:30:00Z" }
      ],
      "unrecognized_faces": 2
    }
  }


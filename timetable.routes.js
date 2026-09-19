const express = require('express');
const pool = require('./db');
const { requireAuth, requireRole } = require('./auth.middleware');

const router = express.Router();

router.use(requireAuth, requireRole('admin'));

const DAYS = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

// إضافة موعد محاضرة لشعبة
router.post('/timetable-slots', async (req, res) => {
  const { section_id, room_id, day_of_week, start_time, end_time } = req.body;

  if (!section_id || !room_id || !day_of_week || !start_time || !end_time) {
    return res.status(400).json({
      error: 'section_id, room_id, day_of_week, start_time and end_time are required',
    });
  }
  if (!DAYS.includes(day_of_week)) {
    return res.status(400).json({ error: `day_of_week must be one of: ${DAYS.join(', ')}` });
  }
  if (end_time <= start_time) {
    return res.status(400).json({ error: 'end_time must be after start_time' });
  }

  try {
    const result = await pool.query(
      `INSERT INTO timetable_slots (section_id, room_id, day_of_week, start_time, end_time)
       VALUES ($1, $2, $3, $4, $5) RETURNING *`,
      [section_id, room_id, day_of_week, start_time, end_time]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    if (err.code === '23503') {
      return res.status(400).json({ error: 'section_id or room_id does not exist' });
    }
    if (err.code === '22007' || err.code === '22P02') {
      return res.status(400).json({ error: 'Invalid time format, use HH:MM' });
    }
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// عرض المواعيد
router.get('/timetable-slots', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM timetable_slots ORDER BY slot_id');
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;
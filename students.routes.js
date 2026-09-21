const express = require('express');
const pool = require('./db');
const { requireAuth, requireRole } = require('./auth.middleware');

const router = express.Router();

// الطلبة بس
router.use(requireAuth, requireRole('student'));

// بيانات الطالب المسجّل دخوله (من الـ token بس، مفيش id بيتبعت)
router.get('/me', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT sp.student_id, sp.student_code, sp.student_name, u.email,
              sp.level, d.department_name
       FROM student_profiles sp
       JOIN users u ON u.user_id = sp.user_id
       LEFT JOIN departments d ON d.department_id = sp.department_id
       WHERE sp.user_id = $1`,
      [req.user.userId]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'No student profile for this user' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;
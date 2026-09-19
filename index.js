const express = require('express');
const pool = require('./db');
const authRoutes = require('./auth.routes');
const adminRoutes = require('./admin.routes');
const peopleRoutes = require('./people.routes');
const timetableRoutes = require('./timetable.routes');
const sessionRoutes = require('./session.routes');
const attendanceRoutes = require('./attendance.routes');
const { requireAuth, requireRole } = require('./auth.middleware');

const app = express();
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.get('/db-check', async (req, res) => {
  try {
    const result = await pool.query('SELECT NOW()');
    res.json({ db: 'connected', time: result.rows[0].now });
  } catch (err) {
    console.error(err);
    res.status(500).json({ db: 'error', message: err.message });
  }
});

app.use('/auth', authRoutes);

app.get('/me', requireAuth, (req, res) => {
  res.json({ userId: req.user.userId, role: req.user.role });
});

app.get('/admin/ping', requireAuth, requireRole('admin'), (req, res) => {
  res.json({ message: 'Welcome, admin' });
});

app.use('/admin', adminRoutes);
app.use('/admin', peopleRoutes);
app.use('/admin', timetableRoutes);
app.use('/sessions', sessionRoutes);
app.use('/attendance', attendanceRoutes);

app.listen(3000, () => {
  console.log('Server running on http://localhost:3000');
});
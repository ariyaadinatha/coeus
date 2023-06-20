const data = request.body;
const query = `SELECT * FROM health_records WHERE id = (${data.id})`;
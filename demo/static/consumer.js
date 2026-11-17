(() => {
  const range = document.querySelector('#progress-range');
  const value = document.querySelector('#progress-value');
  const label = document.querySelector('#progress-label');
  if (range && value && label) {
    range.addEventListener('input', () => { value.value = range.value; label.textContent = `${range.value}%`; });
    value.addEventListener('input', () => { if (value.validity.valid) { range.value = value.value; label.textContent = `${value.value}%`; } });
  }
  const start = document.querySelector('#start-session');
  if (!start) return;
  const status = document.querySelector('#play-status');
  const quality = document.querySelector('#quality');
  let heartbeat = null;
  let running = false;
  let device;
  try { device = localStorage.getItem('mn-device') || crypto.randomUUID(); localStorage.setItem('mn-device', device); }
  catch (_) { device = `browser-${Math.random().toString(36).slice(2)}`; }
  async function authorize() {
    const data = new URLSearchParams({csrf: start.dataset.csrf, profile_id: start.dataset.profile, device_id: device, video_quality: quality.value});
    const response = await fetch('/play-session', {method: 'POST', body: data, credentials: 'same-origin'});
    if (response.redirected) { window.location.assign(response.url); throw new Error('Bạn cần đăng nhập lại.'); }
    if (!response.ok) {
      if (response.status === 403) throw new Error('Gói đã hết hạn, hồ sơ không hợp lệ hoặc chất lượng vượt giới hạn gói.');
      if (response.status === 409) throw new Error('Đã đạt giới hạn thiết bị đồng thời. Hãy đợi phiên cũ hết hạn.');
      throw new Error('Không mở được phiên xem. Vui lòng thử lại.');
    }
    return response.json();
  }
  function failed(error) {
    if (heartbeat) clearInterval(heartbeat);
    heartbeat = null; running = false; start.disabled = false; start.textContent = '▶ Thử lại'; quality.disabled = false; status.textContent = error.message;
  }
  start.addEventListener('click', async () => {
    if (running) return;
    start.disabled = true; status.textContent = 'Đang kiểm tra gói dịch vụ và thiết bị…';
    try {
      const result = await authorize(); running = true; quality.disabled = true; start.textContent = '✓ Phiên đang hoạt động';
      status.textContent = `Phiên ${quality.value} đã được cấp quyền. Kéo thanh tiến độ rồi bấm “Lưu tiến độ” để mô phỏng xem.`;
      heartbeat = setInterval(() => { authorize().catch(failed); }, result.heartbeat_seconds * 1000);
    } catch (error) { failed(error); }
  });
  window.addEventListener('pagehide', () => { if (heartbeat) clearInterval(heartbeat); });
})();

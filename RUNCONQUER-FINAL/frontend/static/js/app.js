/**
 * RunConquer — App Utilities
 * Common functions used across pages: auth state, toasts, navigation.
 */

// --- Auth State ---

function initApp() {
  const token = getToken();
  const user = getUser();

  const authBtn = document.getElementById('nav-auth-btn');
  const userInfo = document.getElementById('nav-user-info');

  if (token && user) {
    if (authBtn) authBtn.classList.add('hidden');
    if (userInfo) {
      userInfo.classList.remove('hidden');
      const avatar = document.getElementById('nav-avatar');
      const username = document.getElementById('nav-username');
      if (avatar) {
        avatar.textContent = user.username ? user.username[0].toUpperCase() : '?';
        if (user.avatar_color) avatar.style.background = user.avatar_color;
      }
      if (username) username.textContent = user.username || 'User';
    }
  } else {
    if (authBtn) authBtn.classList.remove('hidden');
    if (userInfo) userInfo.classList.add('hidden');
  }
}

function requireAuth() {
  if (!getToken()) {
    window.location.href = '/login';
    return false;
  }
  initApp();
  return true;
}

function handleLogout() {
  clearAuth();
  showToast('Logged out successfully', 'info');
  setTimeout(() => window.location.href = '/', 500);
}

// --- Toast Notifications ---

function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast toast-' + type;

  const icons = { success: '✅', error: '❌', info: 'ℹ️', achievement: '🏅' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s ease-in forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

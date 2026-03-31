/**
 * RunConquer — Game Engine (Frontend)
 * XP, levels, ranks, achievements display logic.
 */

// --- Level & XP ---

function calculateLevel(totalXP) {
  if (totalXP <= 0) return 1;
  return Math.max(1, Math.floor(Math.sqrt(totalXP / 100)));
}

function getXPProgress(totalXP) {
  const level = calculateLevel(totalXP);
  const currentLevelXP = (level ** 2) * 100;
  const nextLevelXP = ((level + 1) ** 2) * 100;
  const percent = ((totalXP - currentLevelXP) / (nextLevelXP - currentLevelXP)) * 100;
  return {
    level,
    currentLevelXP,
    nextLevelXP,
    percent: Math.min(100, Math.max(0, percent))
  };
}

// --- Ranks ---

function getRank(level) {
  if (level >= 51) return 'Emperor';
  if (level >= 31) return 'Warlord';
  if (level >= 16) return 'Conqueror';
  if (level >= 6) return 'Explorer';
  return 'Scout';
}

function getRankInfo(rank) {
  const ranks = {
    Scout:    { icon: '🥉', color: '#fbbf24', cssClass: 'rank-scout' },
    Explorer: { icon: '🥈', color: '#cbd5e1', cssClass: 'rank-explorer' },
    Conqueror:{ icon: '🥇', color: '#fbbf24', cssClass: 'rank-conqueror' },
    Warlord:  { icon: '💎', color: '#38bdf8', cssClass: 'rank-warlord' },
    Emperor:  { icon: '👑', color: '#c084fc', cssClass: 'rank-emperor' }
  };
  return ranks[rank] || ranks.Scout;
}

// --- XP Calculations ---

function xpForRun(distanceKm, newTerritory, defended) {
  let xp = 100; // base
  xp += Math.floor(distanceKm * 50);
  if (newTerritory) xp += 200;
  if (defended) xp += 150;
  return xp;
}

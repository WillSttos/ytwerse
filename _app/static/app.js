/**
 * YTWERSE — Frontend Application
 * Modern SaaS Design + Auto-Analyze + Queue + i18n
 */

// ============================================================
// State
// ============================================================

const AppState = {
    IDLE: 'idle',
    ANALYZING: 'analyzing',
    READY: 'ready',
};

let state = AppState.IDLE;
let videoInfo = null;
let analyzeTimeout = null;

// ============================================================
// DOM Elements
// ============================================================

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const dom = {
    urlInput: $('#url-input'),
    analyzeSpinner: $('#analyze-spinner'),
    errorWrapper: $('#error-wrapper'),
    errorMessage: $('#error-message'),
    retryBtn: $('#retry-btn'),

    mainGrid: $('#main-content-grid'),

    infoCard: $('#info-card'),
    infoThumbnail: $('#info-thumbnail'),
    infoTitle: $('#info-title'),
    infoUploader: $('#info-uploader'),
    infoDuration: $('#info-duration'),
    infoPlaylistBadge: $('#info-playlist-badge'),
    infoPlaylistCount: $('#info-playlist-count'),

    formatCard: $('#format-card'),
    formatTabs: $$('.format-tab'),
    videoOptions: $('#video-options'),
    audioOptions: $('#audio-options'),
    videoQuality: $('#video-quality'),
    audioFormat: $('#audio-format'),

    downloadBtn: $('#download-btn'),
    toastContainer: $('#toast-container'),

    // Visual Clipper
    clipperCard: $('#clipper-card'),
    optClipActive: $('#opt-clip-active'),
    clipperBody: $('#clipper-body'),
    clipperSliderWrapper: $('#clipper-slider-wrapper'),
    sliderFill: $('#slider-fill'),
    sliderStart: $('#slider-start'),
    sliderEnd: $('#slider-end'),
    labelStart: $('#label-start'),
    labelEnd: $('#label-end'),
    clipStartInput: $('#clip-start-input'),
    clipEndInput: $('#clip-end-input'),

    // Advanced options
    optSubtitles: $('#opt-subtitles'),
    subtitleOptions: $('#subtitle-options'),
    optSubLangs: $('#opt-sub-langs'),
    optAutoSubs: $('#opt-auto-subs'),
    optEmbedSubs: $('#opt-embed-subs'),
    optThumbnail: $('#opt-thumbnail'),
    optMetadata: $('#opt-metadata'),
    optCookies: $('#opt-cookies'),
    cookieOptions: $('#cookie-options'),
    optCookiesBrowser: $('#opt-cookies-browser'),
    cookieFileContainer: $('#cookie-file-container'),
    cookieFileInput: $('#cookie-file-input'),
    cookieFileName: $('#cookie-file-name'),
    optConcurrent: $('#opt-concurrent'),
    concurrentOptions: $('#concurrent-options'),
    optFragments: $('#opt-fragments'),

    // Queue
    queueBtn: $('#queue-btn'),
    queueBadge: $('#queue-badge'),
    queueSidebar: $('#queue-sidebar'),
    closeQueueBtn: $('#close-queue'),
    queueList: $('#queue-list'),
    queueEmpty: $('#queue-empty'),
    clearCompletedBtn: $('#clear-completed-btn'),
};

// ============================================================
// State Management
// ============================================================

function setState(newState) {
    state = newState;
    updateUI();
}

function updateUI() {
    const isAnalyzing = state === AppState.ANALYZING;
    dom.analyzeSpinner.hidden = !isAnalyzing;
    dom.urlInput.disabled = isAnalyzing;
    dom.downloadBtn.disabled = state === AppState.ANALYZING || state === AppState.IDLE;
    dom.downloadBtn.style.opacity = dom.downloadBtn.disabled ? '0.5' : '1';
    dom.downloadBtn.style.cursor = dom.downloadBtn.disabled ? 'not-allowed' : 'pointer';
    dom.mainGrid.hidden = state !== AppState.READY;
}

// ============================================================
// Advanced Options
// ============================================================

function parseTimeToSeconds(timeStr) {
    if (!timeStr || !timeStr.trim()) return null;
    const parts = timeStr.trim().split(':').map(n => parseInt(n, 10));
    if (parts.some(isNaN)) return null;
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    if (parts.length === 1) return parts[0];
    return null;
}

function formatSecondsToTime(totalSeconds) {
    if (isNaN(totalSeconds) || totalSeconds === null) return '00:00:00';
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = Math.floor(totalSeconds % 60);
    return [h, m, s].map(n => String(n).padStart(2, '0')).join(':');
}

function getAdvancedOptions() {
    const opts = {};
    if (dom.optClipActive.checked) {
        const start = parseTimeToSeconds(dom.clipStartInput.value);
        const end = parseTimeToSeconds(dom.clipEndInput.value);
        const maxVal = parseInt(dom.sliderStart.max, 10);
        if (start > 0 || (maxVal && end < maxVal)) {
            opts.start_time = start;
            opts.end_time = end;
        }
    }
    if (dom.optSubtitles?.checked) {
        opts.subtitles = true;
        opts.sub_langs = dom.optSubLangs?.value || 'pt.*,en';
        opts.auto_subs = dom.optAutoSubs?.checked || false;
        opts.embed_subs = dom.optEmbedSubs?.checked || false;
    }
    if (dom.optThumbnail?.checked) opts.embed_thumbnail = true;
    if (dom.optMetadata?.checked) opts.embed_metadata = true;
    if (dom.optCookies?.checked) {
        const cookiesBrowser = dom.optCookiesBrowser?.value || '';
        opts.cookies_browser = cookiesBrowser;
        if (cookiesBrowser === 'custom' && window.cookiesFileContent) {
            opts.cookies_content = window.cookiesFileContent;
        }
    }
    if (dom.optConcurrent.checked) {
        opts.concurrent_fragments = parseInt(dom.optFragments.value, 10);
    }
    return opts;
}

function setupAdvancedOptions() {
    dom.optSubtitles?.addEventListener('change', () => {
        if (dom.subtitleOptions) dom.subtitleOptions.hidden = !dom.optSubtitles.checked;
    });
    dom.optCookies?.addEventListener('change', (e) => {
        if (dom.cookieOptions) dom.cookieOptions.hidden = !e.target.checked;
    });
    dom.optCookiesBrowser?.addEventListener('change', (e) => {
        if (dom.cookieFileContainer) {
            dom.cookieFileContainer.style.display = e.target.value === 'custom' ? 'block' : 'none';
        }
    });
    dom.cookieFileInput?.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            if (dom.cookieFileName) dom.cookieFileName.textContent = file.name;
            const reader = new FileReader();
            reader.onload = (evt) => { window.cookiesFileContent = evt.target.result; };
            reader.readAsText(file);
        } else {
            if (dom.cookieFileName) dom.cookieFileName.textContent = 'Nenhum arquivo selecionado';
            window.cookiesFileContent = '';
        }
    });
    dom.optConcurrent.addEventListener('change', () => {
        dom.concurrentOptions.hidden = !dom.optConcurrent.checked;
    });
}

// ============================================================
// URL Analysis
// ============================================================

function handleUrlInput() {
    const url = dom.urlInput.value.trim();
    if (!url) { setState(AppState.IDLE); hideError(); return; }
    const isYoutube = url.includes('youtube.com') || url.includes('youtu.be');
    if (!isYoutube) return;
    clearTimeout(analyzeTimeout);
    analyzeTimeout = setTimeout(() => analyzeURL(url), 600);
}

async function analyzeURL(url) {
    if (state === AppState.ANALYZING) return;
    hideError();
    setState(AppState.ANALYZING);
    const cookiesBrowser = dom.optCookies?.checked ? dom.optCookiesBrowser?.value : '';
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, cookies_browser: cookiesBrowser,
                cookies_content: (cookiesBrowser === 'custom') ? window.cookiesFileContent : undefined }),
        });
        const data = await response.json();
        if (!response.ok || data.error) {
            showError(data.error || t('error_invalid'));
            setState(AppState.IDLE);
            return;
        }
        videoInfo = data;
        displayVideoInfo(data);
        setState(AppState.READY);
    } catch (err) {
        showError('Erro de conexão com o servidor. Verifique se o YTWERSE está rodando.');
        setState(AppState.IDLE);
    }
}

function displayVideoInfo(info) {
    if (info.thumbnail) {
        dom.infoThumbnail.src = info.thumbnail;
        dom.infoThumbnail.style.display = 'block';
    } else {
        dom.infoThumbnail.style.display = 'none';
    }
    dom.infoTitle.textContent = info.title || 'Sem título';
    dom.infoUploader.textContent = info.uploader || '';
    dom.clipperCard.style.display = 'none';
    dom.optClipActive.checked = false;
    dom.clipperBody.hidden = true;

    let durationSec = info.duration;
    let durationString = '';
    if (typeof durationSec === 'string' && durationSec.includes(':')) {
        durationString = durationSec;
        const parts = durationSec.split(':').reverse();
        let secs = 0;
        for (let i = 0; i < parts.length; i++) secs += parseInt(parts[i]) * Math.pow(60, i);
        durationSec = secs;
    } else if (durationSec && !isNaN(durationSec)) {
        const mins = Math.floor(durationSec / 60);
        const secs = Math.floor(durationSec % 60);
        durationString = `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    const durationWrapper = dom.infoDuration.parentElement;
    if (info.type === 'playlist') {
        durationSec = null;
        dom.infoDuration.textContent = '';
        if (durationWrapper) durationWrapper.style.display = 'none';
        dom.infoPlaylistBadge.style.display = 'inline-flex';
        dom.infoPlaylistCount.textContent = `${info.count} vídeos`;
    } else {
        dom.infoDuration.textContent = durationString;
        if (durationWrapper) durationWrapper.style.display = durationString ? 'flex' : 'none';
        dom.infoPlaylistBadge.style.display = 'none';
        dom.clipperCard.style.display = 'block';
        if (durationSec && !isNaN(durationSec)) {
            dom.clipperSliderWrapper.style.display = 'block';
            dom.sliderStart.max = durationSec;
            dom.sliderEnd.max = durationSec;
            dom.sliderStart.value = 0;
            dom.sliderEnd.value = durationSec;
            updateClipperUI();
        } else {
            dom.clipperSliderWrapper.style.display = 'none';
            dom.clipStartInput.value = '';
            dom.clipEndInput.value = '';
        }
    }

    dom.videoQuality.innerHTML = '';
    const qualities = info.available_qualities || ['1080p', '720p', '480p', '360p'];
    qualities.forEach((q, index) => {
        const opt = document.createElement('option');
        opt.value = index === 0 ? 'best' : q;
        let label = q;
        if (q === '1080p') label = 'Full HD — 1080p';
        else if (q === '720p') label = 'HD — 720p';
        else if (q === '480p') label = 'SD — 480p';
        else if (q === '360p') label = 'Low — 360p';
        opt.textContent = index === 0 ? `🏆 ${label} (Melhor disponível)` : label;
        if (index === 0) opt.selected = true;
        dom.videoQuality.appendChild(opt);
    });
    selectFormatTab('video');
}

// ============================================================
// Format Selection
// ============================================================

function selectFormatTab(tab) {
    dom.formatTabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    dom.videoOptions.classList.toggle('visible', tab === 'video');
    dom.audioOptions.classList.toggle('visible', tab === 'audio');
}

function getSelectedFormat() {
    const activeTab = document.querySelector('.format-tab.active');
    const mediaType = activeTab ? activeTab.dataset.tab : 'video';
    return mediaType === 'video'
        ? { type: 'video', quality: dom.videoQuality.value }
        : { type: 'audio', audio_format: dom.audioFormat.value };
}

// ============================================================
// Queue Management & Download
// ============================================================

let pollInterval = null;
let notifiedCompleted = new Set();

function toggleQueueSidebar() {
    dom.queueSidebar.classList.toggle('open');
}

async function startDownload() {
    if (!videoInfo) return;
    hideError();
    const format = getSelectedFormat();
    const advancedOpts = getAdvancedOptions();
    const payload = {
        url: videoInfo.url,
        title: videoInfo.title,
        type: format.type,
        quality: format.quality || 'best',
        audio_format: format.audio_format || 'mp3_320',
        is_playlist: videoInfo.type === 'playlist',
        playlist_title: videoInfo.type === 'playlist' ? videoInfo.title : null,
        entries: videoInfo.type === 'playlist' ? videoInfo.entries : [],
        options: advancedOpts,
    };
    try {
        const response = await fetch('/start-download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            showError(errData.error || 'Erro ao iniciar o download.');
            return;
        }
        dom.urlInput.value = '';
        setState(AppState.IDLE);
        if (!dom.queueSidebar.classList.contains('open')) toggleQueueSidebar();
        startPolling();
    } catch (err) {
        showError('Conexão perdida com o servidor.');
    }
}

function startPolling() {
    if (pollInterval) return;
    pollInterval = setInterval(async () => {
        try {
            const res = await fetch('/progress');
            if (!res.ok) return;
            const data = await res.json();
            renderQueue(data.groups || []);
        } catch (e) { /* retry next tick */ }
    }, 600);
}

// ============================================================
// Queue Rendering — Group-based with individual items
// ============================================================

function statusIcon(status) {
    switch (status) {
        case 'complete':    return '<span class="qi-status-dot dot-complete" title="Concluído">✓</span>';
        case 'downloading': return '<span class="qi-status-dot dot-downloading"></span>';
        case 'processing':  return '<span class="qi-status-dot dot-processing"></span>';
        case 'error':       return '<span class="qi-status-dot dot-error" title="Erro">!</span>';
        case 'cancelled':   return '<span class="qi-status-dot dot-cancelled" title="Cancelado">×</span>';
        case 'waiting':     return '<span class="qi-status-dot dot-waiting"></span>';
        default:            return '<span class="qi-status-dot dot-waiting"></span>';
    }
}

// Track per-group collapsed state
const collapsedGroups = new Set();
const seenInactiveGroups = new Set();

function renderQueue(groups) {
    const hasGroups = groups && groups.length > 0;
    dom.queueEmpty.style.display = hasGroups ? 'none' : 'block';

    let activeCount = 0;
    let hasInactive = false;
    if (hasGroups) {
        for (const g of groups) {
            if (g.is_active) activeCount++;
            else hasInactive = true;
        }
    }

    dom.queueBadge.style.display = activeCount > 0 ? 'flex' : 'none';
    dom.queueBadge.textContent = activeCount;
    if (dom.clearCompletedBtn) {
        dom.clearCompletedBtn.style.display = hasInactive ? 'flex' : 'none';
    }

    if (!hasGroups) {
        document.querySelectorAll('.queue-group').forEach(el => el.remove());
        if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
        return;
    }

    // Remove stale groups
    const currentGroupIds = new Set(groups.map(g => g.group_id));
    document.querySelectorAll('.queue-group').forEach(el => {
        if (!currentGroupIds.has(el.dataset.gid)) el.remove();
    });

    // Sort: active first, then inactive
    const sorted = [...groups].sort((a, b) => {
        if (a.is_active === b.is_active) return 0;
        return a.is_active ? -1 : 1;
    });

    sorted.forEach((group, sortedIdx) => {
        let groupEl = document.querySelector(`.queue-group[data-gid="${group.group_id}"]`);
        const isNew = !groupEl;

        if (isNew) {
            groupEl = document.createElement('div');
            groupEl.className = 'queue-group';
            groupEl.dataset.gid = group.group_id;

            const isPlaylist = group.type === 'playlist';
            const isCollapsed = !group.is_active; // completed groups start collapsed
            if (isCollapsed) collapsedGroups.add(group.group_id);

            groupEl.innerHTML = `
                <div class="queue-group-header" role="button" tabindex="0">
                    <div class="queue-group-header-top">
                        <div class="queue-group-left">
                            <span class="qg-chevron ${isCollapsed ? 'collapsed' : ''}">&#9660;</span>
                            <span class="qg-group-status-dot"></span>
                            <span class="queue-group-icon">${isPlaylist ? '\uD83C\uDFB5' : '\u25B6'}</span>
                            <span class="queue-group-title">${escapeHtml(group.title)}</span>
                        </div>
                        <div class="queue-group-actions">
                            <button class="qg-cancel-btn" title="Cancelar grupo">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                            </button>
                        </div>
                    </div>
                    <div class="queue-group-details" style="display:none;"></div>
                </div>
                <div class="queue-group-progress"><div class="queue-group-progress-fill"></div></div>
                <div class="queue-group-items ${isCollapsed ? 'collapsed' : ''}"></div>
            `;

            // Toggle collapse on header click (but not on cancel button)
            groupEl.querySelector('.queue-group-header').addEventListener('click', (e) => {
                if (e.target.closest('.qg-cancel-btn')) return;
                const gid = groupEl.dataset.gid;
                const itemsDiv = groupEl.querySelector('.queue-group-items');
                const chevron = groupEl.querySelector('.qg-chevron');
                if (collapsedGroups.has(gid)) {
                    collapsedGroups.delete(gid);
                    itemsDiv.classList.remove('collapsed');
                    chevron.classList.remove('collapsed');
                } else {
                    collapsedGroups.add(gid);
                    itemsDiv.classList.add('collapsed');
                    chevron.classList.add('collapsed');
                }
            });

            groupEl.querySelector('.qg-cancel-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                cancelGroup(group.group_id, group.is_active);
            });

            dom.queueList.appendChild(groupEl);
        }

        // Maintain DOM order to match sorted array WITHOUT re-appending on every tick
        const children = Array.from(dom.queueList.querySelectorAll('.queue-group'));
        const currentIdx = children.indexOf(groupEl);
        if (currentIdx !== sortedIdx) {
            const referenceNode = dom.queueList.querySelectorAll('.queue-group')[sortedIdx] || null;
            if (referenceNode && referenceNode !== groupEl) {
                dom.queueList.insertBefore(groupEl, referenceNode);
            }
        }

        // Sync collapse state for newly-inactive groups
        if (!group.is_active && !seenInactiveGroups.has(group.group_id)) {
            seenInactiveGroups.add(group.group_id);
            collapsedGroups.add(group.group_id);
            const itemsDiv = groupEl.querySelector('.queue-group-items');
            const chevron = groupEl.querySelector('.qg-chevron');
            if (itemsDiv) itemsDiv.classList.add('collapsed');
            if (chevron) chevron.classList.add('collapsed');
        }

        // Update cancel/remove button
        const cancelBtn = groupEl.querySelector('.qg-cancel-btn');
        if (!group.is_active) {
            cancelBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>`;
            cancelBtn.title = 'Remover da lista';
            cancelBtn.onclick = (e) => { e.stopPropagation(); removeGroup(group.group_id); };
        }

        // Details badge in header
        const detailsEl = groupEl.querySelector('.queue-group-details');
        const completed = group.items.filter(i => i.status === 'complete').length;
        const total = group.items.length;
        
        if (detailsEl) {
            let detailsHtml = '';
            if (group.type === 'playlist') {
                const totalStr = (t('total_items') || 'Total: {total} itens').replace('{total}', total);
                const doneStr = (t('completed_of') || 'Concluídas: {done} de {total}').replace('{done}', completed).replace('{total}', total);
                detailsHtml = `${totalStr} &bull; ${doneStr}`;
            }

            if (completed > 0 || !group.is_active) {
                const openStr = `<span class="qg-open-folder-link">${t('open_folder') || 'Abrir pasta'}</span>`;
                if (detailsHtml) detailsHtml += ' &bull; ';
                detailsHtml += openStr;
            }

            if (detailsHtml) {
                detailsEl.innerHTML = detailsHtml;
                detailsEl.style.display = 'block';
                // Attach click to the new link
                const openLink = detailsEl.querySelector('.qg-open-folder-link');
                if (openLink) {
                    openLink.onclick = (e) => {
                        e.stopPropagation();
                        openFolder(group.media_type, group.playlist_title ? `&playlist=${encodeURIComponent(group.playlist_title)}` : '');
                    };
                }
            } else {
                detailsEl.style.display = 'none';
                detailsEl.innerHTML = '';
            }
        }

        // Group progress bar
        const fillEl = groupEl.querySelector('.queue-group-progress-fill');
        const groupPercent = total > 0 ? Math.round((completed / total) * 100) : 0;
        fillEl.style.width = `${groupPercent}%`;
        if (!group.is_active && completed === total) {
            fillEl.style.background = 'var(--success)';
        } else if (!group.is_active) {
            fillEl.style.background = 'var(--danger)';
        } else {
            fillEl.style.background = '';
        }

        // Group status dot
        const groupDot = groupEl.querySelector('.qg-group-status-dot');
        if (groupDot) {
            let dotClass = 'dot-waiting';
            if (!group.is_active) {
                if (completed === total && total > 0) dotClass = 'dot-complete';
                else dotClass = 'dot-error';
            } else {
                dotClass = 'dot-group-downloading';
            }
            groupDot.className = `qg-group-status-dot ${dotClass}`;
            if (dotClass === 'dot-complete') groupDot.innerHTML = '<span style="color:#fff;font-size:0.55rem;font-weight:bold;">✓</span>';
            else if (dotClass === 'dot-error') groupDot.innerHTML = '<span style="color:#fff;font-size:0.55rem;font-weight:bold;">!</span>';
            else groupDot.innerHTML = '';
        }

        // Render individual items
        const itemsContainer = groupEl.querySelector('.queue-group-items');
        renderGroupItems(itemsContainer, group);
    });
}

function renderGroupItems(container, group) {
    const items = group.items || [];

    // Remove stale item elements
    const currentItemIds = new Set(items.map(i => i.item_id));
    container.querySelectorAll('.queue-item').forEach(el => {
        if (!currentItemIds.has(el.dataset.iid)) el.remove();
    });

    items.forEach((item) => {
        let itemEl = container.querySelector(`.queue-item[data-iid="${item.item_id}"]`);
        const isNew = !itemEl;

        if (isNew) {
            itemEl = document.createElement('div');
            itemEl.className = 'queue-item';
            itemEl.dataset.iid = item.item_id;
            // Build skeleton — we'll patch content below
            itemEl.innerHTML = `
                <div class="qi-row">
                    <span class="qi-status-dot dot-waiting"></span>
                    <div class="qi-info">
                        <span class="qi-title">${escapeHtml(item.title)}</span>
                        <div class="qi-meta">
                            <span class="qi-status-text"></span>
                            <span class="qi-stats"></span>
                        </div>
                    </div>
                    <button class="qi-cancel-btn" title="Cancelar este item" style="display:none">
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>
                </div>
                <div class="qi-progress-bar" style="display:none;">
                    <div class="qi-progress-fill"></div>
                </div>
            `;
            itemEl.querySelector('.qi-cancel-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                cancelItem(group.group_id, item.item_id);
            });
            container.appendChild(itemEl);
        }

        // --- Update only changed data, never recreate the element ---

        // Status class on container
        itemEl.className = `queue-item qi-${item.status}`;

        // Status dot — replace innerHTML of the dot span only
        const dotEl = itemEl.querySelector('.qi-status-dot');
        const newDotClass = `qi-status-dot dot-${item.status}`;
        if (dotEl && dotEl.className !== newDotClass) {
            dotEl.className = newDotClass;
            // Set text content for terminal states
            if (item.status === 'complete') dotEl.textContent = '✓';
            else if (item.status === 'error') dotEl.textContent = '!';
            else if (item.status === 'cancelled') dotEl.textContent = '×';
            else dotEl.textContent = '';
        }

        const statusTextEl = itemEl.querySelector('.qi-status-text');
        const statsEl = itemEl.querySelector('.qi-stats');
        const progressBar = itemEl.querySelector('.qi-progress-bar');
        const progressFill = itemEl.querySelector('.qi-progress-fill');
        const cancelItemBtn = itemEl.querySelector('.qi-cancel-btn');

        // Show per-item cancel button only for active items
        if (cancelItemBtn) {
            cancelItemBtn.style.display = (item.status === 'downloading' || item.status === 'processing' || item.status === 'waiting') && group.is_active ? 'flex' : 'none';
        }

        switch (item.status) {
            case 'waiting':
                statusTextEl.textContent = t('queue_waiting') || 'Aguardando...';
                statsEl.textContent = '';
                progressBar.style.display = 'none';
                break;

            case 'downloading': {
                const pct = item.percent || 0;
                statusTextEl.textContent = pct === 0 ? (t('downloading_state') || 'Baixando...') : `${pct}%`;
                statsEl.textContent = [item.speed, item.eta ? `ETA ${item.eta}` : ''].filter(Boolean).join(' · ');
                progressBar.style.display = 'block';
                progressFill.style.width = `${pct}%`;
                progressFill.style.background = 'var(--accent)';
                break;
            }

            case 'processing':
                statusTextEl.textContent = t('converting') || 'Convertendo...';
                statusTextEl.style.color = '#f97316'; // orange
                statsEl.textContent = '';
                progressBar.style.display = 'block';
                progressFill.style.width = '100%';
                progressFill.style.background = '#f97316';
                break;

            case 'complete':
                statusTextEl.textContent = t('complete') || 'Concluído';
                statusTextEl.style.color = '';
                statsEl.textContent = '';
                progressBar.style.display = 'block';
                progressFill.style.width = '100%';
                progressFill.style.background = 'var(--success)';
                break;

            case 'error':
                statusTextEl.textContent = item.error || 'Erro';
                statusTextEl.style.color = 'var(--danger)';
                statsEl.textContent = '';
                progressBar.style.display = 'block';
                progressFill.style.width = '100%';
                progressFill.style.background = 'var(--danger)';
                break;

            case 'cancelled':
                statusTextEl.textContent = t('cancelled') || 'Cancelado';
                statusTextEl.style.color = '';
                statsEl.textContent = '';
                progressBar.style.display = 'none';
                break;
        }
    });
}

async function cancelGroup(groupId, isActive) {
    try {
        if (isActive) {
            await fetch('/cancel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ group_id: groupId })
            });
            showToast('Grupo cancelado.', 'warning');
        } else {
            await removeGroup(groupId);
        }
    } catch (err) {}
}

async function cancelItem(groupId, itemId) {
    try {
        await fetch('/cancel', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_id: groupId, item_id: itemId })
        });
    } catch (err) {}
}

async function removeGroup(groupId) {
    try {
        await fetch('/clear-group', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group_id: groupId })
        });
        const el = document.querySelector(`.queue-group[data-gid="${groupId}"]`);
        if (el) el.remove();

        const res = await fetch('/progress');
        if (res.ok) renderQueue((await res.json()).groups || []);
    } catch (err) {}
}

async function clearCompleted() {
    try {
        await fetch('/clear-completed', { method: 'POST' });
        const res = await fetch('/progress');
        if (res.ok) renderQueue((await res.json()).groups || []);
    } catch (err) {}
}

async function openFolder(type, playlistParam = '') {
    try {
        await fetch(`/open-folder?type=${type}${playlistParam}`);
    } catch (err) {
        showToast('Não foi possível abrir a pasta.', 'error');
    }
}

// ============================================================
// Error Display
// ============================================================

function showError(message) {
    dom.errorMessage.textContent = message;
    dom.errorWrapper.style.display = 'flex';
}

function hideError() {
    dom.errorWrapper.style.display = 'none';
}

// ============================================================
// Toast Notifications
// ============================================================

let toastIdCounter = 0;

function showToast(message, type = 'success', duration = 5000, actions = []) {
    const id = `toast-${++toastIdCounter}`;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.id = id;

    let actionsHTML = actions.length > 0
        ? `<div class="toast-actions">${actions.map((a, i) => `<button class="btn btn-sm btn-secondary" data-action-idx="${i}">${a.text}</button>`).join('')}</div>`
        : '';

    toast.innerHTML = `
        <div class="toast-body">
            <div class="toast-message">${escapeHtml(message)}</div>
            ${actionsHTML}
        </div>
        <button class="toast-close" aria-label="Fechar">&times;</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => removeToast(id));
    actions.forEach((action, idx) => {
        const btn = toast.querySelector(`[data-action-idx="${idx}"]`);
        if (btn && action.onClick) btn.addEventListener('click', action.onClick);
    });
    dom.toastContainer.appendChild(toast);
    if (duration > 0) setTimeout(() => removeToast(id), duration);
}

function removeToast(id) {
    const toast = document.getElementById(id);
    if (!toast) return;
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// Clipper Logic
// ============================================================

function updateClipperUI() {
    let startVal = parseInt(dom.sliderStart.value, 10);
    let endVal = parseInt(dom.sliderEnd.value, 10);
    const maxVal = parseInt(dom.sliderStart.max, 10);
    if (startVal >= endVal) { startVal = endVal - 1; dom.sliderStart.value = startVal; }
    const leftPercent = (startVal / maxVal) * 100;
    const rightPercent = 100 - ((endVal / maxVal) * 100);
    dom.sliderFill.style.setProperty('--left', `${leftPercent}%`);
    dom.sliderFill.style.setProperty('--right', `${rightPercent}%`);
    const startStr = formatSecondsToTime(startVal);
    const endStr = formatSecondsToTime(endVal);
    dom.labelStart.textContent = startStr;
    dom.labelEnd.textContent = endStr;
    dom.clipStartInput.value = startStr;
    dom.clipEndInput.value = endStr;
}

function syncClipperInputsToSliders() {
    const maxVal = parseInt(dom.sliderStart.max, 10);
    if (!maxVal) return;
    let startSec = parseTimeToSeconds(dom.clipStartInput.value) || 0;
    let endSec = parseTimeToSeconds(dom.clipEndInput.value) || maxVal;
    if (startSec < 0) startSec = 0;
    if (endSec > maxVal) endSec = maxVal;
    if (startSec >= endSec) startSec = endSec - 1;
    dom.sliderStart.value = startSec;
    dom.sliderEnd.value = endSec;
    const leftPercent = (startSec / maxVal) * 100;
    const rightPercent = 100 - ((endSec / maxVal) * 100);
    dom.sliderFill.style.setProperty('--left', `${leftPercent}%`);
    dom.sliderFill.style.setProperty('--right', `${rightPercent}%`);
    dom.labelStart.textContent = formatSecondsToTime(startSec);
    dom.labelEnd.textContent = formatSecondsToTime(endSec);
}

// ============================================================
// Event Listeners
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
    if (window.setLanguage) setLanguage('pt');

    dom.urlInput.addEventListener('input', handleUrlInput);
    dom.urlInput.addEventListener('paste', () => setTimeout(handleUrlInput, 50));

    dom.formatTabs.forEach(tab => {
        tab.addEventListener('click', () => selectFormatTab(tab.dataset.tab));
    });

    dom.downloadBtn.addEventListener('click', startDownload);
    dom.queueBtn.addEventListener('click', toggleQueueSidebar);
    dom.closeQueueBtn.addEventListener('click', toggleQueueSidebar);

    if (dom.clearCompletedBtn) dom.clearCompletedBtn.addEventListener('click', clearCompleted);

    dom.optClipActive.addEventListener('change', () => {
        dom.clipperBody.hidden = !dom.optClipActive.checked;
    });

    dom.sliderStart.addEventListener('input', () => {
        if (parseInt(dom.sliderStart.value) >= parseInt(dom.sliderEnd.value))
            dom.sliderStart.value = parseInt(dom.sliderEnd.value) - 1;
        updateClipperUI();
    });

    dom.sliderEnd.addEventListener('input', () => {
        if (parseInt(dom.sliderEnd.value) <= parseInt(dom.sliderStart.value))
            dom.sliderEnd.value = parseInt(dom.sliderStart.value) + 1;
        updateClipperUI();
    });

    dom.clipStartInput.addEventListener('change', syncClipperInputsToSliders);
    dom.clipEndInput.addEventListener('change', syncClipperInputsToSliders);

    dom.retryBtn.addEventListener('click', () => { hideError(); handleUrlInput(); });

    setupAdvancedOptions();

    // Privacy Modal
    const btnOpenPrivacy = document.getElementById('open-privacy');
    const btnClosePrivacy = document.getElementById('close-privacy');
    const privacyModal = document.getElementById('privacy-modal');
    if (btnOpenPrivacy && btnClosePrivacy && privacyModal) {
        btnOpenPrivacy.addEventListener('click', (e) => { e.preventDefault(); privacyModal.style.display = 'flex'; });
        btnClosePrivacy.addEventListener('click', () => { privacyModal.style.display = 'none'; });
        privacyModal.addEventListener('click', (e) => { if (e.target === privacyModal) privacyModal.style.display = 'none'; });
    }

    const copyDiscordBtn = document.getElementById('copy-discord');
    if (copyDiscordBtn) {
        copyDiscordBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                await navigator.clipboard.writeText('yowerse');
                showToast('Discord (@yowerse) copiado para a área de transferência!', 'success');
            } catch (err) {
                showToast('Não foi possível copiar o Discord.', 'error');
            }
        });
    }

    startPolling();
    dom.urlInput.focus();
});

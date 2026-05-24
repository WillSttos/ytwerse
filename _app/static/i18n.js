const translations = {
    pt: {
        placeholder_url: "Cole a URL do vídeo ou playlist do YouTube aqui...",
        time_clip: "Tempo de Recorte (Opcional)",
        from: "De",
        to: "Para",
        video: "Vídeo",
        audio: "Áudio",
        quality: "Qualidade",
        format: "Formato",
        download_now: "Baixar Agora",
        advanced_options: "Opções Avançadas",
        embed_thumb: "Embutir Thumbnail",
        embed_meta: "Embutir Metadados",
        parallel_dl: "Download Paralelo",
        connections: "Conexões Simultâneas",
        recommended: "recomendado",
        ultra_fast: "ultra rápido",
        privacy: "Privacidade",
        queue_title: "Fila de Downloads",
        queue_empty: "Nenhum download na fila",
        clear_queue: "Limpar Concluídos",
        queue_waiting: "Aguardando...",
        cancelled: "Cancelado",
        complete: "Concluído",
        best_audio: "MP3 — 320 kbps (melhor)",
        good_audio: "MP3 — 192 kbps",
        m4a_audio: "M4A — Melhor qualidade",
        wav_audio: "WAV — Sem compressão",
        opus_audio: "OPUS — Eficiente",
        // Dynamic
        downloading: "Baixando arquivo...",
        processing: "Processando...",
        preparing: "Preparando download",
        error_url: "URL é obrigatória.",
        error_invalid: "URL inválida ou não suportada.",
        playlist: "Playlist",
        cancel: "Cancelar",
        open_folder: "Abrir pasta",
        total_items: "Total: {total} itens",
        completed_of: "Concluídas: {done} de {total}",
        converting: "Convertendo...",
        downloading_state: "Baixando...",
        privacy_title: "Política de Privacidade",
        privacy_body: `<p>O <strong>YTWERSE</strong> é uma interface gráfica local e privada desenhada para ser executada diretamente na sua máquina.</p>
                
                <h3>1. Coleta e Uso de Dados</h3>
                <p>Nós valorizamos a sua privacidade. O YTWERSE <strong>não coleta, armazena, rastreia ou envia</strong> qualquer dado pessoal, histórico de downloads, URLs acessadas ou endereço de IP para nenhum servidor externo. Tudo permanece e é processado exclusivamente no seu computador.</p>
                
                <h3>2. Processamento Local</h3>
                <p>Todo o processo de download, conversão e extração de áudio/vídeo ocorre offline na sua própria máquina usando recursos locais.</p>
                
                <h3>3. Software de Terceiros (YT-DLP)</h3>
                <p>O YTWERSE funciona como um "wrapper" (uma interface visual) para o <strong><a href="https://github.com/yt-dlp/yt-dlp" target="_blank" rel="noopener noreferrer" class="credit-link">yt-dlp</a></strong>, que é um software de código aberto. Durante um download, o yt-dlp se comunica diretamente com os servidores das plataformas (como o YouTube) para obter os arquivos de mídia. Para entender como o tráfego de rede é gerenciado e o que é enviado para essas plataformas de terceiros, consulte a documentação oficial no repositório do yt-dlp.</p>

                <h3>4. Responsabilidade do Usuário</h3>
                <p>O YTWERSE é uma ferramenta neutra. O uso desta aplicação é de total responsabilidade do usuário. Recomendamos fortemente que você respeite os direitos autorais e os Termos de Serviço das plataformas de onde você realiza os downloads.</p>`
    },
    en: {
        placeholder_url: "Paste YouTube video or playlist URL here...",
        time_clip: "Clip Time (Optional)",
        from: "From",
        to: "To",
        video: "Video",
        audio: "Audio",
        quality: "Quality",
        format: "Format",
        download_now: "Download Now",
        advanced_options: "Advanced Options",
        embed_thumb: "Embed Thumbnail",
        embed_meta: "Embed Metadata",
        parallel_dl: "Parallel Download",
        connections: "Concurrent Connections",
        recommended: "recommended",
        ultra_fast: "ultra fast",
        privacy: "Privacy",
        queue_title: "Download Queue",
        queue_empty: "No downloads in queue",
        clear_queue: "Clear Completed",
        queue_waiting: "Waiting...",
        cancelled: "Cancelled",
        complete: "Complete",
        best_audio: "MP3 — 320 kbps (best)",
        good_audio: "MP3 — 192 kbps",
        m4a_audio: "M4A — Best quality",
        wav_audio: "WAV — Uncompressed",
        opus_audio: "OPUS — Efficient",
        // Dynamic
        downloading: "Downloading file...",
        processing: "Processing...",
        preparing: "Preparing download",
        error_url: "URL is required.",
        error_invalid: "Invalid or unsupported URL.",
        playlist: "Playlist",
        cancel: "Cancel",
        open_folder: "Open folder",
        total_items: "Total: {total} items",
        completed_of: "Completed: {done} of {total}",
        converting: "Converting...",
        downloading_state: "Downloading...",
        privacy_title: "Privacy Policy",
        privacy_body: `<p><strong>YTWERSE</strong> is a local and private graphical interface designed to be executed directly on your machine.</p>
                
                <h3>1. Data Collection and Usage</h3>
                <p>We value your privacy. YTWERSE <strong>does not collect, store, track, or send</strong> any personal data, download history, accessed URLs, or IP addresses to any external server. Everything remains and is processed exclusively on your computer.</p>
                
                <h3>2. Local Processing</h3>
                <p>The entire process of downloading, converting, and extracting audio/video occurs offline on your own machine using local resources.</p>
                
                <h3>3. Third-Party Software (YT-DLP)</h3>
                <p>YTWERSE functions as a "wrapper" (a visual interface) for <strong><a href="https://github.com/yt-dlp/yt-dlp" target="_blank" rel="noopener noreferrer" class="credit-link">yt-dlp</a></strong>, which is open-source software. During a download, yt-dlp communicates directly with platform servers (like YouTube) to obtain media files. To understand how network traffic is managed and what is sent to these third-party platforms, please refer to the official documentation in the yt-dlp repository.</p>

                <h3>4. User Responsibility</h3>
                <p>YTWERSE is a neutral tool. The use of this application is entirely the user's responsibility. We strongly recommend that you respect copyright laws and the Terms of Service of the platforms from which you download.</p>`
    }
};

let currentLang = 'pt';

function setLanguage(lang) {
    if (!translations[lang]) return;
    currentLang = lang;
    
    // Update active state in lang selector
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[lang][key]) {
            el.placeholder = translations[lang][key];
        }
    });

    // Update innerHTML
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            // Keep SVG icons if any by wrapping text in span in HTML, or just replace text nodes
            // Best practice: structure HTML to have text in a span with data-i18n
            el.textContent = translations[lang][key];
        }
    });

    // Update innerHTML with HTML content
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        if (translations[lang][key]) {
            el.innerHTML = translations[lang][key];
        }
    });

    // Custom events for dynamic updates
    document.dispatchEvent(new Event('languageChanged'));
}

function t(key) {
    return translations[currentLang][key] || key;
}

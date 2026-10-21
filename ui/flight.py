"""
Module hiệu ứng chuyển động bay Canva (Canva Ghost Flight Animation)
Dành cho việc chọn và bỏ chọn thẻ bài báo nghiên cứu trong Streamlit.
Chạy trực tiếp trên Web Animations API / GPU của trình duyệt (60fps) trong Main Document.
"""

from __future__ import annotations

import streamlit as st


def render_flight_controller() -> None:
    """
    Tiêm client-side script trực tiếp vào main document (không qua iframe sandbox)
    để bắt sự kiện click checkbox và kích hoạt hiệu ứng khối bài báo lướt bay 2 chiều
    (Canva Ghost Flight) mượt mà 60fps.
    """
    flight_html = """
    <div id="rf-flight-root" style="display:none;position:absolute;width:0;height:0;overflow:hidden;">
        <script>
        (function() {
            try {
                if (window.__rfFlightActive) return;
                window.__rfFlightActive = true;
                console.log('[RF Flight] Controller initialized in main DOM');

                document.addEventListener('click', function(e) {
                    const chk = e.target.closest('[data-testid="stCheckbox"]') || e.target.closest('label');
                    if (!chk) return;

                    // Tìm thẻ bài báo cha chứa checkbox này
                    let card = chk.closest('[class*="st-key-card_"]') 
                            || chk.closest('[data-testid="stVerticalBlockBorderWrapper"]');
                    if (!card) {
                        let curr = chk;
                        while (curr && curr !== document.body) {
                            if (curr.querySelector && curr.querySelector('.rf-card-marker')) {
                                card = curr;
                                break;
                            }
                            curr = curr.parentElement;
                        }
                    }
                    if (!card) return;

                    // Xác định trạng thái: đang chọn hay bỏ chọn
                    const marker = card.querySelector('.rf-card-marker');
                    const isSelected = (marker && marker.getAttribute('data-rf-is-selected') === 'true')
                                    || !!card.querySelector('.rf-card-selected-marker')
                                    || !!card.querySelector('.rf-badge-selected');
                    const isSelecting = !isSelected;

                    const startRect = card.getBoundingClientRect();
                    if (startRect.width <= 0 || startRect.height <= 0) return;

                    // Xác định vị trí đích đến
                    let targetRect = null;
                    if (isSelecting) {
                        const targetElem = document.querySelector('#rf-selected-target') 
                                        || document.querySelector('#rf-selected-anchor')
                                        || document.querySelector('[data-testid="stExpander"]')
                                        || document.querySelector('.rf-section-header');
                        if (targetElem) {
                            targetRect = targetElem.getBoundingClientRect();
                        } else {
                            targetRect = { left: startRect.left, top: Math.max(80, startRect.top - 380), width: startRect.width, height: 100 };
                        }
                    } else {
                        const targetElem = document.querySelector('#rf-suggestions-target')
                                        || document.querySelector('.rf-section-header:not(.rf-section-selected)');
                        if (targetElem) {
                            targetRect = targetElem.getBoundingClientRect();
                        } else {
                            targetRect = { left: startRect.left, top: startRect.top + 350, width: startRect.width, height: 100 };
                        }
                    }

                    // Tạo bản sao khối Canva Ghost Card
                    const ghost = card.cloneNode(true);
                    const ghostId = 'rf-flight-ghost-' + Date.now();
                    ghost.id = ghostId;
                    ghost.classList.add('rf-flight-ghost');
                    ghost.classList.add(isSelecting ? 'rf-flight-ghost-selecting' : 'rf-flight-ghost-deselecting');

                    // Vô hiệu hóa mọi link, nút bên trong ghost để không gây side-effect
                    ghost.querySelectorAll('input, button, a, [data-testid]').forEach(function(el) {
                        el.setAttribute('tabindex', '-1');
                        el.style.pointerEvents = 'none';
                    });

                    // Định hình vị trí ban đầu của Ghost Card
                    ghost.style.setProperty('left', startRect.left + 'px', 'important');
                    ghost.style.setProperty('top', startRect.top + 'px', 'important');
                    ghost.style.setProperty('width', startRect.width + 'px', 'important');

                    document.body.appendChild(ghost);

                    // 1. Chừa lại 1 khoảng trống nghỉ rõ ràng tại vị trí bài báo vừa nhấc lên
                    const originalHeight = card.offsetHeight;
                    card.style.boxSizing = 'border-box';
                    card.style.height = originalHeight + 'px';
                    card.style.minHeight = originalHeight + 'px';
                    card.style.maxHeight = originalHeight + 'px';
                    card.style.opacity = '0';
                    card.style.background = 'rgba(255, 255, 255, 0.02)';
                    card.style.border = '1.5px dashed rgba(255, 255, 255, 0.12)';
                    card.style.borderRadius = '16px';
                    card.style.pointerEvents = 'none';

                    const parentWrapper = card.closest('[data-testid="stVerticalBlockBorderWrapper"]') || card.parentElement;
                    if (parentWrapper && parentWrapper !== card && parentWrapper !== document.body) {
                        parentWrapper.style.boxSizing = 'border-box';
                        parentWrapper.style.height = originalHeight + 'px';
                        parentWrapper.style.minHeight = originalHeight + 'px';
                        parentWrapper.style.maxHeight = originalHeight + 'px';
                    }

                    // 2. Nghỉ 1 khoảng (280ms) cho mắt thấy rõ khoảng trống khi bài bay lên,
                    // sau đó các bài ở dưới mới bắt đầu đẩy lên từ từ với tốc độ vừa phải (520ms)
                    setTimeout(function() {
                        card.style.transition = 'all 0.52s cubic-bezier(0.33, 1, 0.68, 1)';
                        card.style.height = '0px';
                        card.style.minHeight = '0px';
                        card.style.maxHeight = '0px';
                        card.style.marginTop = '0px';
                        card.style.marginBottom = '0px';
                        card.style.paddingTop = '0px';
                        card.style.paddingBottom = '0px';
                        card.style.borderWidth = '0px';
                        card.style.overflow = 'hidden';

                        if (parentWrapper && parentWrapper !== card && parentWrapper !== document.body) {
                            parentWrapper.style.transition = 'all 0.52s cubic-bezier(0.33, 1, 0.68, 1)';
                            parentWrapper.style.height = '0px';
                            parentWrapper.style.minHeight = '0px';
                            parentWrapper.style.maxHeight = '0px';
                            parentWrapper.style.margin = '0px';
                            parentWrapper.style.padding = '0px';
                            parentWrapper.style.overflow = 'hidden';
                        }
                    }, 280);

                    // Tính toán vectơ bay
                    const deltaX = (targetRect.left || startRect.left) - startRect.left;
                    const deltaY = (targetRect.top !== undefined ? targetRect.top : (isSelecting ? 100 : startRect.top + 350)) - startRect.top;

                    // Animation rõ nét 100% opacity, chuyển động chậm rãi và gia tốc từ từ
                    const keyframes = isSelecting ? [
                        {
                            transform: 'translate3d(0, 0, 0) scale(1)',
                            opacity: 1,
                            offset: 0
                        },
                        {
                            // Giai đoạn 1 (0 -> 30%): Khởi đầu chậm rãi, nhấc lên mượt mà
                            transform: 'translate3d(' + (deltaX * 0.10) + 'px, ' + (deltaY * 0.12) + 'px, 0) scale(0.985)',
                            opacity: 1,
                            offset: 0.30
                        },
                        {
                            // Giai đoạn 2 (30% -> 70%): Lướt êm ái, rõ nét từng chi tiết
                            transform: 'translate3d(' + (deltaX * 0.65) + 'px, ' + (deltaY * 0.68) + 'px, 0) scale(0.98)',
                            opacity: 1,
                            offset: 0.70
                        },
                        {
                            // Giai đoạn 3 (70% -> 94%): Chèn vào đích chậm rãi và chuẩn xác
                            transform: 'translate3d(' + deltaX + 'px, ' + deltaY + 'px, 0) scale(1)',
                            opacity: 1,
                            offset: 0.94
                        },
                        {
                            // Hoàn tất chuyển giao tại chỗ
                            transform: 'translate3d(' + deltaX + 'px, ' + deltaY + 'px, 0) scale(1)',
                            opacity: 0,
                            offset: 1
                        }
                    ] : [
                        {
                            transform: 'translate3d(0, 0, 0) scale(1)',
                            opacity: 1,
                            offset: 0
                        },
                        {
                            transform: 'translate3d(' + (deltaX * 0.10) + 'px, ' + (deltaY * 0.12) + 'px, 0) scale(0.985)',
                            opacity: 1,
                            offset: 0.30
                        },
                        {
                            transform: 'translate3d(' + (deltaX * 0.65) + 'px, ' + (deltaY * 0.68) + 'px, 0) scale(0.98)',
                            opacity: 1,
                            offset: 0.70
                        },
                        {
                            transform: 'translate3d(' + deltaX + 'px, ' + deltaY + 'px, 0) scale(1)',
                            opacity: 1,
                            offset: 0.94
                        },
                        {
                            transform: 'translate3d(' + deltaX + 'px, ' + deltaY + 'px, 0) scale(1)',
                            opacity: 0,
                            offset: 1
                        }
                    ];

                    try {
                        const anim = ghost.animate(keyframes, {
                            duration: 750,
                            easing: 'cubic-bezier(0.35, 0, 0.15, 1)',
                            fill: 'forwards'
                        });
                        anim.onfinish = function() {
                            try { ghost.remove(); } catch(err) {}
                        };
                    } catch (e) {
                        ghost.remove();
                    }

                    // Tự động dọn dẹp an toàn sau 950ms
                    setTimeout(function() {
                        try {
                            const leftover = document.getElementById(ghostId);
                            if (leftover) leftover.remove();
                        } catch(err) {}
                    }, 950);

                }, true); // Bắt capturing phase để chạy ngay khi click chuột

            } catch (err) {
                console.warn('[RF Flight] Error:', err);
            }
        })();
        </script>
    </div>
    """

    st.html(flight_html, unsafe_allow_javascript=True)


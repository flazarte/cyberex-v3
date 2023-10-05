$(document).ready(function () {

    var waitUntilButtonVisible = function () {
        let isClose = true;

        setTimeout(function () {
            const btn = $("#intergramRoot");

            if (btn.length) {
                const btnWrapper = btn.first();
                const btnWrapperCont = $("#intergramRoot > div");
                const svgIcon = $("#intergramRoot > div > div:nth-child(1) > div:nth-child(2) > svg");
                const chatDiv = $("#intergramRoot > div > div:nth-child(1) > div:nth-child(1)");
                const telegramIcon = `<i class="fab fa-telegram" style="position: absolute; font-size: 63px; left: -19px; top: -6px;"></i>`;

                btnWrapperCont.css({
                    minWidth: "62px",
                    minHeight: "61px",
                    borderRadius: "100%",
                    right: "60px",
                    bottom: "10px",
                    background: "rgb(31, 140, 235)"
                });

                function removeChatText() {
                    chatDiv.css({
                        display: "none"
                    });
                    // Override Icon
                    svgIcon.parent().css({
                        position: "relative"
                    })
                    svgIcon.parent().append(telegramIcon);
                    svgIcon.remove();
                }
                removeChatText();

                function onClickClose() {
                    const header = $("#intergramRoot > div > div:nth-child(1)");
                    header.on('click', () => {
                        const iframe = $("#intergramRoot").find('iframe').parent().is(':visible');
                        if(iframe) $("#intergramRoot > div > div:nth-child(1) > div:nth-child(1)").css({"textTransform": "none"});
                        if(!iframe) waitUntilButtonVisible();

                        if (!isClose) removeChatText();
                            btnWrapperCont.find('i').css({
                                display: (isClose ? 'none' : 'block')
                            });
                        isClose = !isClose;
                    });
                }

                onClickClose();

                clearTimeout(waitUntilButtonVisible);
            } else {
                waitUntilButtonVisible();
            }
        }, 100)
    }
    waitUntilButtonVisible();
});
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.button1');

    // 첫 번째 애니메이션: 버튼들이 중앙 높이로 이동
    setTimeout(() => {
        buttons.forEach(button => {
            button.classList.add('falling'); /* 모든 버튼에 떨어지는 이미지를 추가 */
            button.classList.add('middle'); /* 모든 버튼을 중간 높이로 이동 */
        });
    }, 500); /* 페이지 로딩 후 1초 대기 */

    // 두 번째 애니메이션: 버튼들이 양쪽으로 펼쳐짐
    setTimeout(() => {
        buttons.forEach(button => {
            button.classList.remove('falling'); /* 모든 버튼에서 떨어지는 이미지를 제거 */
        });
        buttons[0].classList.add('left-most'); /* 첫 번째 버튼을 왼쪽으로 이동 */
        buttons[1].classList.add('left'); /* 두 번째 버튼을 왼쪽으로 이동 */
        buttons[2].classList.add('right'); /* 세 번째 버튼을 오른쪽으로 이동 */
        buttons[3].classList.add('right-most'); /* 네 번째 버튼을 오른쪽으로 이동 */
    }, 1500); /* 첫 애니메이션 후 1초 대기 */

    // 마우스 오버와 마우스 아웃 이벤트 추가
    buttons.forEach(button => {
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translate(-50%, -20px)';
        });

        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translate(-50%, 0)';
        });
    });

    const button1 = document.querySelector('.button1');
    const hiddenText = document.querySelector('.hidden-text');

    button1.addEventListener('transitionend', () => {
        if (button1.classList.contains('falling')) {
            hiddenText.classList.add('show');
        }
    });

});

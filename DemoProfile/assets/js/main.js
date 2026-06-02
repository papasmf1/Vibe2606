// 모바일 메뉴 버튼과 네비게이션 영역을 찾는다.
const menuToggle = document.querySelector('.menu-toggle');
const siteNav = document.querySelector('.site-nav');

if (menuToggle && siteNav) {
  // 햄버거 버튼을 누르면 메뉴 열기/닫기를 토글한다.
  menuToggle.addEventListener('click', () => {
    siteNav.classList.toggle('open');
  });

  // 메뉴를 누르면 자동으로 닫히게 해서 사용성을 높인다.
  siteNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      siteNav.classList.remove('open');
    });
  });
}

// 스크롤 등장 효과를 적용할 요소들을 찾는다.
const revealItems = document.querySelectorAll('.reveal');

if ('IntersectionObserver' in window && revealItems.length > 0) {
  // 요소가 화면에 15% 이상 보이면 is-visible 클래스를 붙인다.
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.15,
    }
  );

  revealItems.forEach((item) => observer.observe(item));
} else {
  // 구형 브라우저 대응: 애니메이션 없이 바로 표시
  revealItems.forEach((item) => item.classList.add('is-visible'));
}

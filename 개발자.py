class Developer:
    def __init__(self, name, language, experience):
        self.name = name
        self.language = language
        self.experience = experience  # 경력(년)

    def introduce(self):
        print(
            f"안녕하세요. 저는 {self.name}이며, "
            f"{self.language} 개발자입니다. "
            f"경력은 {self.experience}년입니다."
        )

    def code(self):
        print(f"{self.name}님이 {self.language}로 코드를 작성하고 있습니다.")


# 객체 생성
developer1 = Developer("홍길동", "Python", 5)

# 메서드 호출
developer1.introduce()
developer1.code()
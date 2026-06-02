# 파이썬연습.py

# 변수를 초기화
# 숫자와 문자열을 각각 변수에 담아둔다.
x = 100
y = 200
strA = "문자열을 저장"

# 함수 호출
# dir()은 현재 사용할 수 있는 이름 목록을 보여준다.
print(dir())
# len()은 문자열 길이를 계산한다.
print(len(strA))

# 함수를 하나 정의
# times(a, b)는 a와 b를 곱해서 결과를 돌려준다.
def times(a,b):
    return a*b 

# 함수를 호출
result = times(3,4)
# 계산된 결과를 화면에 출력한다.
print(result)


# Person 클래스를 정의하는데 id, name 변수가 있고,
# 이 값을 출력하는 printInfo() 함수를 정의한다.
class Person:
    # 객체를 만들 때 id와 name 값을 받아서 저장한다.
    def __init__(self, id, name):
        self.id = id
        self.name = name
    
    # 저장된 id와 name을 보기 좋게 출력한다.
    def printInfo(self):
        print("ID:", self.id)
        print("Name:", self.name)

# 인스턴스를 생성
person1 = Person(1, "홍길동")
# 인스턴스의 함수를 호출
# person1 안에 저장된 정보를 화면에 출력한다.
person1.printInfo()



    


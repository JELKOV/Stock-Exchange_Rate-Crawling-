# Stock Market Web Scraper

## 프로젝트 개요
네이버 금융 데이터를 크롤링하여 특정 종목의 주식 정보와 환율 데이터를 수집하는 Python 기반의 웹 스크래핑 프로젝트입니다.
이 프로젝트는 GUI 기반으로 동작하며, 일정한 시간마다 자동으로 크롤링이 실행될 수 있도록 스케줄링 기능을 포함하고 있습니다.

## 주요 기능
- **주식 정보 크롤링**: 네이버 금융에서 특정 종목의 가격, 거래량, 변동률 등 데이터를 수집
- **환율 정보 크롤링**: 네이버 금융의 시장 지수 데이터를 활용하여 현재 환율 및 변동률 수집
- **자동 크롤링 스케줄링**: 하루 특정 시간에 자동으로 크롤링을 실행 (schedule 라이브러리 활용)
- **GUI 지원**: Tkinter 기반의 GUI로 사용자가 직접 종목을 검색하고 크롤링 가능
- **데이터 저장**: 크롤링된 데이터를 CSV 파일에 저장 및 업데이트

## 프로젝트 구조
```
StockMarketScraper/
│── main.py                 # 메인 실행 파일 (GUI 및 크롤링 기능 포함)
│── requirements.txt        # 필요한 Python 패키지 목록
│── stocks.txt              # 자동 크롤링할 종목 코드 리스트
│── kospi_stock_codes.csv   # 크롤링된 KOSPI 종목 코드 데이터
│── stock_exchange_data.csv # 수집된 주식 및 환율 데이터 저장 파일
│── README.md               # 프로젝트 설명 문서
```

## 실행 방법
### 1. 가상 환경 생성 및 패키지 설치
```bash
# 가상 환경 생성
python -m venv .venv

# 가상 환경 활성화 (Windows)
.venv\Scripts\activate

# 가상 환경 활성화 (Mac/Linux)
source .venv/bin/activate

# 필수 패키지 설치
pip install -r requirements.txt
```

### 2. 프로젝트 실행
```bash
python main.py
```

## 스케줄링 기능
현재 프로젝트는 `schedule` 라이브러리를 활용하여 다음 시간에 자동 실행됩니다.
- 오전 9시
- 오전 9시 30분
- 오후 3시
- 오후 6시

자동 실행되는 종목 코드는 `stocks.txt` 파일에서 관리됩니다.
해당 파일을 직접 수정하여 원하는 종목을 추가할 수 있습니다.

## 사용 기술
- **Python**: 크롤링 및 데이터 처리
- **Selenium**: 웹 자동화 및 데이터 크롤링
- **Tkinter**: GUI 인터페이스 제공
- **Pandas**: 데이터 저장 및 처리
- **Schedule**: 자동화 스케줄링 기능 구현

## 주의 사항
1. 실행 전에 Chrome 브라우저 및 ChromeDriver가 설치되어 있어야 합니다.
2. `CHROME_DRIVER_PATH`를 실행 환경에 맞게 수정해야 합니다.
3. 네이버 금융 사이트의 변경에 따라 크롤링 로직 수정이 필요할 수 있습니다.

## 개발자
JELKOV


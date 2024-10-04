# Satisfactory Discord Bot

이 프로젝트는 Satisfactory 게임 서버의 상태를 모니터링하고 Discord 채널에 정보를 제공하는 봇입니다.

## 기능

- 서버의 운영 시간(uptime) 확인
- 서버 플레이 타임 랭킹 확인
- 서버 상태 변경 시 Discord 알림

  ![1728002325163](image/README/1728002325163.png)

## 설치

1. **리포지토리 클론**

   ```bash
   git clone https://github.com/pkhkr/satisfactory-discord-bot.git
   cd satisfactory-discord-bot
   ```
2. **환경 설정**

   `docker-compose.yml` 파일에서 환경 변수를 설정합니다. 다음과 같은 형식으로 설정할 수 있습니다:

   ```yaml
   version: '3'

   services:
     satisfactory-bot:
       build: .
       environment:
         - DISCORD_TOKEN=your_discord_token
         - SERVER_ADDRESS=your_server_address
         - SERVER_PORT=your_server_port
         - LOG_PATH=/app/logs/FactoryGame.log
         - DISCORD_CHANNEL_ID=your_discord_channel_id
         - MAX_PLAYERS=maximum_number_of_players
       volumes:
         - my_logs/FactoryGame.log:/app/logs/FactoryGame.log
   ```
3. **도커(Docker) 사용**

   도커를 사용하여 봇을 실행할 수 있습니다. `docker-compose.yml` 파일을 사용하여 컨테이너를 빌드하고 실행합니다.

   ```bash
   docker-compose up --build -d
   ```

## 사용법

- Discord에서 `!uptime` 명령어를 사용하여 서버의 운영 시간을 확인할 수 있습니다.
- `!ranking` 명령어를 사용하여 서버의 플레이 타임 랭킹을 확인할 수 있습니다.

  ![1728002269895](image/README/1728002269895.png)

## 코드 구조

- `satisfactory/log_tracer.py`: 로그 파일을 처리하고 서버 상태를 추적하는 클래스가 포함되어 있습니다.
- `satisfactory/cogs/uptime.py`: 서버의 운영 시간을 확인하는 Discord 명령어가 정의되어 있습니다.
- `satisfactory/cogs/ranking.py`: 서버의 플레이 타임 랭킹을 확인하는 Discord 명령어가 정의되어 있습니다.
- `satisfactory/database.py`: 서버와 플레이어 정보를 저장하고 불러오는 데이터베이스 관련 함수가 포함되어 있습니다.

## TODO

- 콘솔 채널 연동: 서버의 콘솔 출력을 Discord 채널로 실시간 전송하는 기능 구현
- 채팅 연동: 게임 내 채팅과 Discord 채널 간의 양방향 통신 기능 추가
- 서버 상태 모니터링: 서버의 CPU, 메모리 사용량 등을 주기적으로 확인하고 보고하는 기능 개발

## 기여

기여를 원하신다면, 이 리포지토리를 포크하고 풀 리퀘스트를 보내주세요.

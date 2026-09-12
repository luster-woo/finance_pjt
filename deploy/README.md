# 배포

AWS EC2 에 Docker Compose 로 배포한다. 아래는 실제로 수행한 순서를 그대로 적은 것이다.
막힌 지점과 원인은 `배포일지.md` 에 따로 기록했다.

```
브라우저 :80
   |
 nginx  --- /            -> Vue dist (SPA)
        --- /api/*       -> gunicorn (접두사 제거)
        --- /admin/      -> gunicorn
        --- /static/     -> collectstatic 결과
        --- /media/      -> 업로드 파일
              |
            web (Django + gunicorn) --- db (PostgreSQL 16)
            sched (APScheduler)     ---/
```

외부에 열리는 포트는 80 하나다. DB 와 gunicorn 은 도커 네트워크 안에만 있고 호스트에
포트를 내주지 않는다.

## 실제 배포 환경

| 항목 | 값 |
|---|---|
| 클라우드 | AWS EC2 (ap-northeast-2 서울) |
| 인스턴스 | t3.small — 2 vCPU / 1.9GiB |
| OS | Ubuntu Server 24.04.4 LTS (x86_64) |
| 스토리지 | EBS gp3 8GiB → **20GiB 로 확장** (5단계) |
| 스왑 | 4GB |
| Docker | 29.8.0 / Compose v5.5.1 |
| 요금제 | AWS Free plan — 크레딧 소진 시 계정이 닫힐 뿐 과금되지 않는다 |

## 0. 로컬 리허설

**서버에 올리기 전에 로컬에서 운영 구성을 그대로 한 번 띄웠다.** 이 단계를 먼저 한 덕분에
서버에서는 애플리케이션 레벨 문제를 한 건도 만나지 않았고, 인프라 문제만 상대하면 됐다.

```bash
cp .env.prod.example .env.prod   # SECRET_KEY, POSTGRES_PASSWORD 만 채우면 된다
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
curl -I http://localhost
```

여기서 확인한 것:

- `migrate` 전체 적용, `collectstatic` 154개 파일 복사
- `/` 가 200 이고 응답 HTML 이 `/assets/index-*.js` 를 참조하는지 (해시 없는 경로를
  참조하면 `FE/public/index.html` 잔재가 빌드 산출물을 덮어쓴 것이다)
- `/api/products/` 200 — nginx `proxy_pass` 의 접두사 제거가 동작하는지
- `/static/admin/css/base.css` 200 — 볼륨 공유가 맞는지
- `sched` 로그에 `[scheduler] APScheduler 시작` 이 찍히는지

서버에서 첫 빌드는 10분 가까이 걸린다. 오타 하나 잡는 데 그 시간을 다시 쓰지 않으려면
로컬에서 먼저 통과시켜 두는 편이 빠르다.

## 1. 인스턴스 생성

EC2 > 인스턴스 > 인스턴스 시작

| 항목 | 값 |
|---|---|
| 이름 | `finfit` |
| AMI | **Ubuntu Server 24.04 LTS (HVM), SSD Volume Type** |
| 인스턴스 유형 | t3.small |
| 키 페어 | 새로 생성 > RSA > `.pem` 다운로드 |
| 스토리지 | 20 GiB gp3 |

AMI 는 목록 상단의 `Ubuntu` 타일을 누르는 것만으로 정해지지 않는다. 타일은 OS 계열
필터일 뿐이고 실제 선택은 그 아래 드롭다운이다. 기본값이 SQL Server 가 포함된 유료
이미지로 잡혀 있으면 인스턴스 시작 자체가 거부된다 (배포일지 #1).
이름이 `... SSD Volume Type` 으로 끝나고 `프리 티어 사용 가능` 라벨이 붙은 것을 고른다.

**보안 그룹** — 인바운드 규칙 두 개가 필요하다.

| 유형 | 포트 | 소스 |
|---|---|---|
| SSH | 22 | 내 IP |
| HTTP | 80 | 0.0.0.0/0 |

생성 마법사에서 HTTP 규칙이 누락되기 쉽다. 나중에 보안 그룹에서 추가해도 즉시 반영되므로
재시작은 필요 없다 (배포일지 #4).

## 2. 접속

`.pem` 은 권한이 열려 있으면 ssh 가 거부한다. PowerShell 에서 상속을 끊고 읽기만 남긴다.

```powershell
icacls .\finfit-key.pem /inheritance:r
icacls .\finfit-key.pem /grant:r "$env:USERNAME:(R)"
ssh -i .\finfit-key.pem ubuntu@<퍼블릭IP>
```

세부 정보 탭에는 **퍼블릭 IPv4** 와 **프라이빗 IPv4** 가 나란히 있다. `172.31.x.x` 는
VPC 내부 주소라 밖에서 닿지 않는다. 접속에 쓰는 것은 퍼블릭 쪽이다.

`Permission denied (publickey)` 는 대개 사용자명 문제다. Ubuntu AMI 는 `ubuntu`,
Amazon Linux 는 `ec2-user`.

## 3. Docker

```bash
sudo apt-get update
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit
```

그룹 변경은 **재접속해야 반영된다.** 리눅스 그룹은 로그인 시점에 결정되므로 이미 열려 있는
세션에는 적용되지 않는다. 재접속 후 `docker ps` 가 sudo 없이 되면 완료다.

## 4. 스왑

메모리 2GiB 에서 `npm run build` 는 스왑 없이 OOM 으로 죽을 수 있다. 커널이 죽이는 것이라
애플리케이션 로그에는 아무것도 남지 않는다.

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h
```

## 5. 디스크 확장

**스왑 파일은 디스크를 그만큼 차지한다.** 기본 8GiB EBS 에 4GB 스왑을 만들면 남는 공간이
200MB 대로 떨어져 도커 빌드가 `no space left on device` 로 실패한다 (배포일지 #2).
1단계에서 20GiB 로 만들었다면 이 단계는 건너뛴다.

콘솔에서 EC2 > Elastic Block Store > 볼륨 > 작업 > **볼륨 수정** > 크기 20 > 수정.
볼륨을 키워도 OS 는 예전 크기를 그대로 알고 있으므로 **파티션과 파일시스템을 따로 넓혀야
한다.** 무중단으로 가능하다.

```bash
sudo growpart /dev/nvme0n1 1    # 파티션 확장
sudo resize2fs /dev/nvme0n1p1   # 파일시스템 확장
df -h /
```

## 6. 코드와 환경변수

```bash
git clone https://github.com/luster-woo/finance_pjt.git finfit && cd finfit
cp .env.prod.example .env.prod
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # SECRET_KEY
nano .env.prod
```

최소 네 줄은 채워야 한다. 외부 API 키는 비워도 기동되며 해당 기능만 동작하지 않는다.

```
SECRET_KEY=<생성한 값>
ALLOWED_HOSTS=<퍼블릭IP>
CSRF_TRUSTED_ORIGINS=http://<퍼블릭IP>
POSTGRES_PASSWORD=<임의의 강한 값>
```

`ALLOWED_HOSTS` 는 `DEBUG=False` 가 되는 순간부터 검사된다. 비워두면 Django 가 Host
헤더를 거부해 400 을 낸다.

## 7. 기동

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.prod ps
```

`--env-file` 은 `up` 뿐 아니라 `ps` · `logs` · `exec` 에도 붙여야 한다. 빼면 compose 가
`POSTGRES_DB is missing a value` 로 변수 보간에 실패한다.

첫 빌드는 10분 안팎. 컨테이너 네 개(db/web/sched/nginx)가 Up 이면 된다.
마이그레이션과 `collectstatic` 은 `BE/entrypoint.sh` 가 처리하므로 따로 실행하지 않는다.

관리자 계정:

```bash
C=$(docker compose -f docker-compose.prod.yml --env-file .env.prod ps -q web)
docker exec -it $C python manage.py createsuperuser
```

FinLife 키를 넣었다면 상품 데이터도 수집한다.

```bash
docker exec -it $C python manage.py load_data
```

## 8. 검증

**안에서 밖으로 한 겹씩 확인한다.** 안쪽이 200 이면 그 구간은 전부 용의선상에서 지워진다.

```bash
# 1) 서버 안에서
curl -I http://localhost                      # nginx / SPA
curl -s -o /dev/null -w "%{http_code}\n" -H "Host: <퍼블릭IP>" http://localhost/api/products/
```

`Host` 헤더를 주는 이유는 `ALLOWED_HOSTS` 에 퍼블릭 IP 만 넣었기 때문이다. 그냥
`curl http://localhost/api/...` 를 하면 Host 가 `localhost` 로 가서 400 이 난다.
정적 파일을 서빙하는 `/` 와 `/static/` 은 nginx 가 직접 처리하므로 200 이 나오고,
Django 로 넘어가는 경로만 400 이 나는 식으로 갈린다 (배포일지 #3).

```bash
# 2) 밖에서
curl -s -o /dev/null -w "%{http_code}\n" http://<퍼블릭IP>/
```

실제 결과:

| 경로 | 응답 | 응답시간 |
|---|---|---|
| `/` | 200 | 0.38s |
| `/api/products/` | 200 | 0.40s |
| `/api/news/` | 200 | 0.42s |
| `/admin/` | 302 | 0.42s |
| `/static/admin/css/base.css` | 200 | 0.59s |
| `/products/1` (SPA 폴백) | 200 | 0.40s |

컨테이너 메모리 실측 합계는 469MB 다 (web 305 / sched 102 / db 58 / nginx 4).
디스크는 이미지 포함 8.5GB 를 썼다.

admin 로그인은 CSRF 토큰을 받아 POST 까지 확인했다. 302 와 함께 `sessionid` 쿠키가
내려오고, 그 쿠키로 `/admin/` 이 200 이면 `CSRF_TRUSTED_ORIGINS` 가 제대로 잡힌 것이다.

## 9. 재배포

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

마이그레이션은 entrypoint 가 처리한다.

## 10. 문제 해결

| 증상 | 확인 |
|---|---|
| 인스턴스 시작 거부 (`SQL Server is not supported...`) | AMI 드롭다운이 SQL Server 포함 이미지다. `SSD Volume Type` 으로 바꾼다 |
| 빌드 `no space left on device` | `df -h /`. 스왑이 디스크를 먹은 것이다. 5단계 |
| 빌드가 조용히 죽음 (exit 137) | `dmesg` 의 `killed process` 기록 확인 → OOM. 4단계 스왑 |
| 브라우저 무한 로딩 | 서버 안에서 `curl -I http://localhost`. 200이면 보안 그룹 인바운드 80 |
| Bad Request (400) | `ALLOWED_HOSTS` 에 접속 주소 추가 후 `up -d` |
| compose 가 `POSTGRES_DB is missing` | 모든 compose 명령에 `--env-file .env.prod` |
| API 전부 404 | nginx `proxy_pass http://backend/;` 끝 슬래시 |
| 새로고침 시 404 | nginx `try_files $uri $uri/ /index.html;` |
| 화면 백지, `/src/main.js` 404 | `FE/public/index.html` 잔재. `git rm` |
| admin CSS 깨짐 | `docker exec <web> ls /app/staticfiles`, `docker exec <nginx> ls /vol/static` |
| admin 로그인 CSRF 오류 | `CSRF_TRUSTED_ORIGINS` 에 스킴 포함해 추가 |
| 업로드 413 | nginx `client_max_body_size` |
| `exec /app/entrypoint.sh: no such file` | CRLF. Dockerfile 에서 줄바꿈을 LF 로 바꾸고 실행 권한을 준다 |
| 뉴스/시세 갱신 안 됨 | `logs -f sched` 에 `[scheduler] APScheduler 시작` 확인 |

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod logs --tail 100 web
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f sched
```

## 11. 정리

확인이 끝나면 리소스를 남기지 않는다. Free plan 은 과금되지 않지만 크레딧은 소모된다.

1. EC2 > 인스턴스 > **인스턴스 종료(Terminate)** — 중지(Stop)가 아니다. Stop 은 EBS 가 남는다
2. EC2 > 볼륨 — 남은 EBS 가 없는지 확인 (루트 볼륨은 종료 시 함께 삭제된다)
3. EC2 > **탄력적 IP** — 할당받았다면 릴리스. 연결되지 않은 EIP 는 과금 대상이다
4. 스냅샷 / AMI 가 없는지 확인
5. 다른 리전에 만든 리소스는 목록에 보이지 않으므로 사용한 리전을 확인한다

계정 자체는 닫지 않는 편이 낫다. AWS 는 동일인의 중복 계정 생성을 막으므로, 닫으면 다시
만들 때 심사에서 거절될 수 있다.

## 12. HTTPS

이번 배포에서는 붙이지 않았다. 붙이려면 보안 그룹에 443 을 추가한 뒤:

```bash
sudo apt install -y certbot
docker compose -f docker-compose.prod.yml stop nginx
sudo certbot certonly --standalone -d <도메인>
docker compose -f docker-compose.prod.yml start nginx
```

nginx 서비스에 `/etc/letsencrypt:/etc/letsencrypt:ro` 를 마운트하고 `nginx.conf` 에
443 server 블록을 추가한 뒤 `.env.prod` 에서 `SECURE_SSL_REDIRECT=True` 로 바꾼다.
인증서 없이 먼저 켜면 무한 리다이렉트가 된다.

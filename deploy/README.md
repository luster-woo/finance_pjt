# 배포

Oracle Cloud 프리티어 VM에 Docker Compose로 배포한다.

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

외부에 열리는 포트는 80 하나다. DB와 gunicorn은 도커 네트워크 안에만 있다.

## 1. VM

Compute > Instances > Create instance

- Image: Ubuntu 22.04
- Shape: VM.Standard.A1.Flex (Ampere), 2 OCPU / 12GB — Always Free
- SSH keys: Generate a key pair for me (개인키 보관)

A1 용량이 없으면 리전을 바꾸거나 시간을 두고 재시도한다. E2.1.Micro(1GB)로도 되지만
메모리가 부족해 빌드가 죽으므로 4단계 스왑이 필수다.

## 2. 접속

```powershell
icacls .\ssh-key.key /inheritance:r
icacls .\ssh-key.key /grant:r "$env:USERNAME:(R)"
ssh -i .\ssh-key.key ubuntu@<IP>
```

`Permission denied (publickey)` 는 대개 사용자명 문제다. Ubuntu 이미지는 `ubuntu`,
Oracle Linux는 `opc`.

## 3. Docker

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit
```

그룹 변경은 재접속해야 반영된다. 재접속 후:

```bash
docker --version
docker compose version
```

## 4. 스왑

메모리 2GB 이하 인스턴스에서는 `npm run build` 와 pandas 설치가 OOM으로 죽는다.

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 5. 코드

```bash
git clone <레포> finfit && cd finfit
cp .env.prod.example .env.prod
nano .env.prod
```

최소 `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `POSTGRES_PASSWORD` 는 채워야 한다.

## 6. 방화벽

Oracle Cloud는 방화벽이 두 겹이다. 둘 다 열어야 한다.

**콘솔** — VCN > Security Lists > Default Security List > Add Ingress Rule

```
Source CIDR: 0.0.0.0/0   Protocol: TCP   Port: 80
```

**인스턴스** — Ubuntu 이미지는 기본으로 80을 DROP 한다.

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save
```

`netfilter-persistent save` 를 빼면 재부팅 시 되돌아간다.

## 7. 기동

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml logs -f web
```

첫 빌드는 5~15분 걸린다. 초기 데이터:

```bash
C=$(docker compose -f docker-compose.prod.yml ps -q web)
docker exec -it $C python manage.py createsuperuser
docker exec -it $C python manage.py load_data
docker exec -it $C python manage.py loaddata accounts/user_data.json
```

로컬 개발 데이터를 그대로 옮기려면:

```bash
# 로컬
python manage.py dumpdata --exclude contenttypes --exclude auth.permission \
  --natural-foreign --natural-primary --indent 2 > dump.json
# 서버
docker exec -i $C python manage.py loaddata /dev/stdin < dump.json
```

`--exclude contenttypes` 를 빼면 PK 충돌로 IntegrityError 가 난다.

## 8. 문제 해결

| 증상 | 확인 |
|---|---|
| 브라우저 무한 로딩 | 서버 안에서 `curl -I http://localhost`. 200이면 6단계 방화벽 문제 |
| Bad Request (400) | `ALLOWED_HOSTS` 에 접속 주소 추가 |
| API 전부 404 | nginx `proxy_pass http://backend/;` 끝 슬래시 |
| 새로고침 시 404 | nginx `try_files $uri $uri/ /index.html;` |
| 화면 백지, `/src/main.js` 404 | `FE/public/index.html` 잔재. `git rm` |
| admin CSS 깨짐 | `docker exec web ls /app/staticfiles`, `docker exec nginx ls /vol/static` |
| admin 로그인 CSRF 오류 | `CSRF_TRUSTED_ORIGINS` 에 스킴 포함해 추가 |
| 업로드 413 | nginx `client_max_body_size` |
| 빌드가 조용히 죽음 | `dmesg \| grep -i "killed process"`. 4단계 스왑 |
| `exec /app/entrypoint.sh: no such file` | CRLF. `git config core.autocrlf input` |
| 뉴스/시세 갱신 안 됨 | `logs -f sched` 에 `[scheduler] APScheduler 시작` 확인 |

```bash
docker compose -f docker-compose.prod.yml logs --tail 100 web
docker compose -f docker-compose.prod.yml exec web sh
```

## 9. 재배포

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

마이그레이션은 entrypoint 가 처리한다.

## 10. HTTPS

Security List와 iptables에 443을 추가한 뒤:

```bash
sudo apt install -y certbot
docker compose -f docker-compose.prod.yml stop nginx
sudo certbot certonly --standalone -d <도메인>
docker compose -f docker-compose.prod.yml start nginx
```

nginx 서비스에 `/etc/letsencrypt:/etc/letsencrypt:ro` 를 마운트하고 `nginx.conf` 에
443 server 블록을 추가한 뒤 `.env.prod` 에서 `SECURE_SSL_REDIRECT=True` 로 바꾼다.
인증서 없이 먼저 켜면 무한 리다이렉트가 된다.

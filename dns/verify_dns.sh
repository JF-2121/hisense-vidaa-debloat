#!/bin/sh
# Prüft vom MacBook aus (gleiche öffentliche IP = gleiches NextDNS-Profil), ob die Regeln greifen.
# Nutzung: sh dns/verify_dns.sh <DNS-Filter-IP, z. B. die NextDNS-Linked-IP>
S=${1:?NextDNS-IP angeben}
FAIL=0
chk(){ out=$(dig +time=3 +tries=2 @"$S" "$1" A)
  if [ -z "$(echo "$out" | grep 'status:')" ]; then v=TIMEOUT
  else r=$(echo "$out" | awk '$4=="A"{print $5}' | tail -1); case "$r" in 0.0.0.0|"") v=GEBLOCKT;; *) v="frei ($r)";; esac; fi
  ok=OK; [ "$v" = TIMEOUT ] && ok=WARN
  { [ "$2" = BLOCK ] && [ "${v%% *}" = frei ]; } && ok=FEHLER; { [ "$2" = ALLOW ] && [ "$v" = GEBLOCKT ]; } && ok=FEHLER
  [ $ok = FEHLER ] && FAIL=1
  printf '%-7s %-6s %-42s %s\n' "$ok" "$2" "$1" "$v"; }
for d in tvmodules-vidaa.vidaahub.com rsc-ads.vidaahub.com rpt-mntz-azure.vidaahub.com recommend-ui.vidaahub.com \
         recommend-ui-eu.vidaahub.com detail-ui-eu.vidaahub.com content-recommendation.hismarttv.com api-recommendation-eu.hismarttv.com \
         ter-jrnl-eu.vidaahub.com eligibility-panelresearch.googlevideo.com tracking-vss.vidaahub.com abtest-tv.vidaahub.com api.eu.hismarttv.com; do chk $d BLOCK; done
for d in img.vidaahub.com www.netflix.com api-global.netflix.com assets.nflxext.com www.youtube.com youtubei.googleapis.com \
         i.ytimg.com www.primevideo.com atv-ps-eu.amazon.com m.media-amazon.com; do chk $d ALLOW; done
exit $FAIL

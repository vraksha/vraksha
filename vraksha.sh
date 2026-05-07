#!/bin/bash

# ==============================================================================
# Vraksha CLI · runtime initializer
# ==============================================================================

INSTALL_PATH="/usr/local/bin/vraksha"
SCRIPT_PATH="$(realpath "$0")"
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")

# palette
A='\033[38;2;0;212;170m'   # accent · teal
A2='\033[38;2;0;143;114m'  # accent · soft
M='\033[38;5;244m'         # muted
D='\033[38;5;238m'         # dim
T='\033[38;5;254m'         # text
B='\033[1m'                # bold
DIM='\033[2m'              # faint
R='\033[38;5;203m'         # red
Y='\033[38;5;215m'         # warn
G='\033[38;5;121m'         # success
NC='\033[0m'

# glyphs 
GL_LOGO="▲"
GL_DOT="·"
GL_CHECK="✓"
GL_ARROW="›"
GL_DIAMOND="◆"

# state
STATUS_FILE=$(mktemp)
CURRENT_PHASE="resolving"
FORCE_BUILD=false

# arguments
for arg in "$@"; do
    case $arg in
        -b|--build) FORCE_BUILD=true ;;
        -h|--help)
            printf "\n  ${A}${B}${GL_LOGO}${NC}  ${B}${T}vraksha${NC}   ${M}CLI help${NC}\n"
            printf "  ${D}────────────────────────────────────────────────────────────────${NC}\n"
            printf "  ${T}Usage:${NC} vraksha ${D}[options]${NC}\n\n"
            printf "  ${A}${B}Options:${NC}\n"
            printf "    ${T}-b, --build${NC}    ${M}Force rebuild of the runtime environment${NC}\n"
            printf "    ${T}-h, --help${NC}     ${M}Show this help message${NC}\n"
            printf "\n"
            exit 0
            ;;
    esac
done

cleanup() {
    rm -f "$STATUS_FILE"
    tput cnorm 2>/dev/null
}
trap cleanup EXIT
trap "exit 1" SIGINT SIGTERM

# helpers
term_width() { tput cols 2>/dev/null || echo 80; }

hr() {
    local w=$(term_width)
    printf "${D}"
    printf '─%.0s' $(seq 1 "$w")
    printf "${NC}\n"
}

print_header() {
    local w=$(term_width)
    printf "\n"
    printf "  ${A}${B}${GL_LOGO}${NC}  ${B}${T}vraksha${NC}   ${M}runtime initializer${NC}\n"
    printf "  ${D}"
    printf '─%.0s' $(seq 1 $((w - 4)))
    printf "${NC}\n\n"
}

# global spinner 
start_global_spinner() {
    (
        local frames=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
        local i=0
        tput civis
        while [ -f "$STATUS_FILE" ]; do
            local raw_status=$(cat "$STATUS_FILE")
            local phase="${raw_status%%|*}"
            local detail="${raw_status#*|}"

            local term_w=$(term_width)
            local prefix_len=$(echo -n "  ⠋  $phase  $GL_DOT  " | wc -c)
            local max_detail_len=$(( term_w - prefix_len - 4 ))

            detail=$(echo "$detail" | tr -d '\r\n')
            if [ ${#detail} -gt $max_detail_len ]; then
                detail="${detail:0:$((max_detail_len-3))}..."
            fi

            if [ -n "$phase" ]; then
                if [ -n "$detail" ]; then
                    printf "\r\033[K  ${A}%s${NC}  ${B}${T}%s${NC}  ${D}%s${NC}  ${M}%s${NC}" \
                        "${frames[$i]}" "$phase" "$GL_DOT" "$detail"
                else
                    printf "\r\033[K  ${A}%s${NC}  ${B}${T}%s${NC}" \
                        "${frames[$i]}" "$phase"
                fi
            fi
            sleep 0.1
            i=$(( (i + 1) % 10 ))
        done
        tput cnorm
    ) &
    SPINNER_PID=$!
}

stop_global_spinner() {
    local final_msg=$1
    rm -f "$STATUS_FILE"
    wait $SPINNER_PID 2>/dev/null
    if [ -n "$final_msg" ]; then
        printf "\r\033[K  ${G}${GL_CHECK}${NC}  ${B}${T}%s${NC}\n" "$final_msg"
    fi
}

# == 1. workspace check ==================================================
cd "$SCRIPT_DIR"

print_header

if ! docker info &> /dev/null; then
    printf "  ${R}✗${NC}  ${B}docker is not running${NC}  ${M}or you lack permissions${NC}\n\n"
    exit 1
fi

ENV_FOUND=false
for f in .env.local .env; do
    if [ -f "$f" ]; then
        ENV_FOUND=true
        break
    fi
done

if [ "$ENV_FOUND" = false ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        printf "  ${G}${GL_CHECK}${NC}  ${T}created${NC} ${B}.env.local${NC} ${M}from template${NC}\n"
        printf "  ${Y}${GL_ARROW}${NC}  ${M}edit ${NC}${B}.env.local${NC}${M} with your api keys before running again${NC}\n\n"
        exit 0
    else
        printf "  ${R}✗${NC}  ${B}missing environment file${NC}  ${M}in ${SCRIPT_DIR}${NC}\n\n"
        exit 1
    fi
fi

# == 2. build & initialize ==============================================

# Check if a rebuild is actually needed
REBUILD_NEEDED=$FORCE_BUILD
if [ "$REBUILD_NEEDED" = false ]; then
    # Get the image ID for the vraksha service
    IMAGE_ID=$(docker compose images -q vraksha 2>/dev/null)
    if [ -z "$IMAGE_ID" ]; then
        REBUILD_NEEDED=true
    fi
fi

if [ "$REBUILD_NEEDED" = true ]; then
    BUILD_LOG=$(mktemp)
    printf "  ${A}${GL_DIAMOND}${NC}  ${B}${T}initializing runtime${NC}  ${D}${GL_DOT}${NC}  ${M}docker compose build${NC}\n\n"

    echo "preparing|" > "$STATUS_FILE"
    start_global_spinner

    docker compose build --progress plain 2>&1 | while IFS= read -r line; do
        [[ -z "${line// }" ]] && continue
        [[ "$line" == "#"* ]] && [[ "$line" != *"#"* ]] && continue

        NEW_PHASE=""
        case "$line" in
            *"load build definition"*) NEW_PHASE="loading build definitions" ;;
            *"load metadata"*)         NEW_PHASE="fetching container metadata" ;;
            *"install"*)               NEW_PHASE="installing dependencies" ;;
            *"exporting"*)             NEW_PHASE="exporting image layers" ;;
            *"naming to"*)             NEW_PHASE="finalizing containers" ;;
        esac

        if [ -n "$NEW_PHASE" ] && [ "$NEW_PHASE" != "$CURRENT_PHASE" ]; then
            if [ "$CURRENT_PHASE" != "resolving" ] && [ "$CURRENT_PHASE" != "preparing" ]; then
                printf "\r\033[K  ${G}${GL_CHECK}${NC}  ${B}${T}%s${NC}\n" "$CURRENT_PHASE"
            fi
            CURRENT_PHASE="$NEW_PHASE"
        fi

        DETAIL=$(echo "$line" | sed -E 's/^#[0-9]+ //; s/^[0-9]+.[0-9]+s //' | xargs)

        echo "$CURRENT_PHASE|$DETAIL" > "$STATUS_FILE"
        echo "$line" >> "$BUILD_LOG"
    done

    BUILD_STATUS=${PIPESTATUS[0]}

    stop_global_spinner "$CURRENT_PHASE"

    if [ $BUILD_STATUS -ne 0 ]; then
        printf "\n  ${R}✗${NC}  ${B}failed to build vraksha soul${NC}\n\n"
        cat "$BUILD_LOG"
        rm -f "$BUILD_LOG"
        exit 1
    fi
    rm -f "$BUILD_LOG"
    printf "\n  ${G}${GL_CHECK}${NC}  ${B}${T}vraksha soul initialized${NC}\n"
else
    printf "  ${G}${GL_CHECK}${NC}  ${B}${T}runtime environment ready${NC}  ${M}(using existing image)${NC}\n"
    printf "  ${D}${GL_DOT}${NC}  ${M}tip: use ${NC}${T}--build${NC}${M} to force a refresh${NC}\n"
fi

# (Build status already reported above)
printf "  ${A}${GL_ARROW}${NC}  ${M}launching agent interface${NC}\n"

# subtle handoff line into the python TUI
hr

# == 3. launch agent ===========================================
docker compose run --rm --remove-orphans vraksha 2> >(grep -vE "Creating|Created|Starting|Started|Network" >&2)

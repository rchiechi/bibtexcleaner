#!/bin/bash


#SET OUTPUT AND TMP DIRECTORY#####
OUTDIR="${HOME}/Desktop/"
TMPDIR="LaTeX"

# MISC
LC_CTYPE=C
BASENAME=$(basename "$PWD")

##########################
RED=$(tput setaf 1 2>/dev/null)
GREEN=$(tput setaf 2 2>/dev/null)
YELLOW=$(tput setaf 3 2>/dev/null)
LIME_YELLOW=$(tput setaf 190 2>/dev/null)
POWDER_BLUE=$(tput setaf 153 2>/dev/null)
BLUE=$(tput setaf 4 2>/dev/null)
MAGENTA=$(tput setaf 5 2>/dev/null)
CYAN=$(tput setaf 6 2>/dev/null)
WHITE=$(tput setaf 7 2>/dev/null)
BRIGHT=$(tput bold 2>/dev/null)
BLINK=$(tput blink 2>/dev/null)
REVERSE=$(tput smso 2>/dev/null)
UNDERLINE=$(tput smul 2>/dev/null)
RS=$(tput sgr0 2>/dev/null)

#######################

#
# NOTE: May not work if filenames have spaces in them!
#

usage() {
	echo "${LIME_YELLOW}Usage: $0 [ -z ] [ -j ] [ -o OUTDIR ] .tex <.tex> ... ${RS}"
}

exit_abnormal() {
    usage
    exit 1
}

finddeps () {
	pdflatex -draft -record -halt-on-error "$1" >/dev/null 
	awk '!x[$0]++' ${1%.tex}.fls | sed '/^INPUT \/.*/d' | sed '/^OUTPUT .*/d' | sed '/^PWD .*/d' | sed 's/^INPUT //g'
}



if [ ! -n "$1" ]; then
    usage
    exit 0
fi

ZIP=0
BZ=0

while getopts ":o:zj" options; do
    case "${options}" in
        z) 
            ZIP=1
            ;;
        j)
            BZ=1
            ;;
        o)
            OUTDIR="${OPTARG}"
            ;;
        :)
            echo "${RED}Error: -${OPTARG} requires an argument."
            exit_abnormal
            ;;
        *)
            exit_abnormal
            ;;
        esac
done

# Convert OUTDIR to absolute path
OUTDIR=$(cd "$OUTDIR"; pwd)

if [[ ! -d "$OUTDIR" ]]; then
    echo "${RED}${OUTDIR} is not a directory!"
    exit_abnormal
fi

if [[ $ZIP == 0 && $BZ == 0 ]]; then
    echo "${RED}You must pick at least one archive option, -z / -j.${RS}"
    exit_abnormal
fi


if [[ ! -d "${TMPDIR}" ]] ; then mkdir "${TMPDIR}"; fi
if [ $? != 0 ] ; then
	echo "Error creating ${TMPDIR} exiting."
	exit 1
fi

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
for TEX in $@
do
    if [[ -d "${TEX}" ]]; then
        if [[ "$OUTDIR" != $(cd "$TEX"; pwd) ]]; then
            echo "${YELLOW}Skipping directory $TEX"
        fi
        continue
    fi
	echo ${TEX} | grep -q \.tex
	if [[ "$?" == 0 ]] ; then
		echo "Finding deps for ${TEX}"
		finddeps "${TEX}" | xargs -n 1 -I % rsync -q --relative % "${TMPDIR}"
	    BIB=$(grep '\\bibliography' manuscript.tex | cut -d '{' -f 2 | sed 's+}+.bib+')
        if [[ -f "$BIB" ]] ; then
            echo "Adding $BIB"
            cp "${BIB}" "${TMPDIR}"
        fi
    elif [[ -f "${TEX}" ]]; then
		cp "${TEX}" "${TMPDIR}"
	fi
done
IFS=$SAVEIFS

cd "${TMPDIR}"
if [ $? == 0 ]
then
	echo "${LIME_YELLOW}Removing comments from *.tex${RS}"
	printf '%s\0' *.tex | xargs -0 -n 1 sed -i.bak '/^%.*$/d'
	rm *.out *.bak 2>/dev/null
    if [[ $ZIP == 1 ]]; then
        echo "${POWDER_BLUE}Compressing files to ${OUTDIR}${BASENAME}.zip${RS}"
        zip -r9 "${OUTDIR}${BASENAME}.zip" *
    fi
    if [[ $BZ == 1 ]]; then
        echo "${POWDER_BLUE}Compressing files to ${OUTDIR}${BASENAME}.tar.bz2${RS}"
        tar -cjvf "${OUTDIR}${BASENAME}.tar.bz2" *
    fi
    cd ..
	rm -fr "${TMPDIR}"
else
	echo "${RED}Error enterting temp dir ${TMPDIR}${RS}"
	exit 1
fi

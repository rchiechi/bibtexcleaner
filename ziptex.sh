#!/bin/bash

# If you use a custom class file, put it here
CUSTOM_CLASS="${HOME}/Documents/work/Manuscripts/BibLaTex-Template/rcclab.cls"

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
  echo "${LIME_YELLOW}Usage: $0 [ -f] [ -z ] [ -j ] [ -o OUTDIR ] .tex <.tex> ... ${RS}"
}

exit_abnormal() {
  usage
  exit 1
}

finddeps() {
  pdflatex -draft -record -halt-on-error "$1" >/dev/null
  awk '!x[$0]++' ${1%.tex}.fls | sed '/^INPUT \/.*/d' | sed '/^OUTPUT .*/d' | sed '/^PWD .*/d' | sed 's/^INPUT //g'
}

checktex() { # This function should only be called from $TMPDIR
  local __texok=0
  for TEX in ${TEXFILES[@]}; do
    pdflatex -draft -halt-on-error "${TEX}" >/dev/null
    if [[ $? == 0 ]]; then
      echo "${GREEN}${TEX} is OK.${RS}"
    else
      echo "${RED}${TEX} is NOT OK.${RS}"
      __texok=1
    fi
  done
  return $__texok
}

catclass() { # This function should only be called from $TMPDIR
  # Check for CUSTOM_CLASS
  [[ -z ${CUSTOM_CLASS} ]] && return
  # If a copy of the cls file exists locally, use that one
  [[ -f $(basename ${CUSTOM_CLASS}) ]] && classfile=$(basename ${CUSTOM_CLASS}) || classfile=${CUSTOM_CLASS}
  for TEX in ${TEXFILES[@]}; do
    grep '\\documentclass' "${TEX}" | grep -q $(basename ${classfile} | sed 's/\.cls//g')
    if [[ $? == 0 ]]; then
      echo "${LIME_YELLOW}Concatenating $(basename ${classfile}) into ${TEX} for portability.${RS}"
      mv "${TEX}" "${TEX}.orig"
      printf "\\\begin{filecontents}{$(basename ${classfile})}\n" > "${TEX}"
      cat "${classfile}" >> "${TEX}"
      printf "\\\end{filecontents}\n" >> "${TEX}"
      cat "${TEX}.orig" >> "${TEX}"
      rm "${TEX}.orig"
      [[ "$classfile" != "${CUSTOM_CLASS}" ]] && echo "$classfile" >> .todel
    fi
  done
}

cataux() { # This function should only be called from $TMPDIR
  for TEX in ${TEXFILES[@]}; do
    ls *.aux | while read aux; do
      #grep -q "${aux%.*}" ${TEX}
      egrep -q ".*?\{\s*${aux%.*}\s*\}.*?" "${TEX}"
      if [[ $? == 0 ]]; then
        echo "${LIME_YELLOW}Concatenating $(basename ${aux}) into ${TEX} files for portability.${RS}"
        mv "${TEX}" "${TEX}.orig"
        printf "\\\begin{filecontents}{$(basename ${aux})}\n" > "${TEX}"
        cat "${aux}" >> "${TEX}"
        printf "\\\end{filecontents}\n" >> "${TEX}"
        cat "${TEX}.orig" >> "${TEX}"
        rm "${TEX}.orig"
        echo "${aux}" >> .todel
      fi
    done
  done
}

flattendirs() { # This function should only be called from $TMPDIR
  for TEX in ${TEXFILES[@]}; do
    echo "${LIME_YELLOW}Flattening directory structure for ${TEX}.${RS}"
    _gfxpath=$(grep graphicspath ${TEX}| cut -d '{' -f '2-' | tr -d '{}/')
    if [[ ! -d "${_gfxpath}" ]]; then
      ls
      echo "${RED} Warning: graphicspath \"${_gfxpath}\" not found (could be a case-sensitivity issue!"
    else
      find "$_gfxpath" \
        -depth -type f -exec mv -v "{}" ./ \;
    fi
    sed -i.bak '/\\graphicspath.*/d' "${TEX}"
  done
  find ./ -depth -type d -empty -delete
}



if [ ! -n "$1" ]; then
  usage
  exit 0
fi

ZIP=0
BZ=0
FORCE=0

while getopts ":o:zjf" options; do
  case "${options}" in
    z)
      ZIP=1
      ;;
    j)
      BZ=1
      ;;
    f)
      FORCE=1
      ;;
    o)
      OUTDIR="${OPTARG}"
      ;;
    :)
      echo "${RED}Error: -${OPTARG} requires an argument.${RS}"
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
  echo "${RED}${OUTDIR} is not a directory!${RS}"
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

TEXFILES=()

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")
for TEX in $@
do
  if [[ -d "${TEX}" ]]; then
    if [[ "$OUTDIR" != $(cd "$TEX"; pwd) ]]; then
      echo "${YELLOW}Skipping directory ${TEX}${RS}"
    fi
    continue
  fi
  echo ${TEX} | grep -q \.tex
  if [[ "$?" == 0 ]] ; then
    TEXFILES+=($TEX)
    echo "Finding deps for ${TEX}"
    finddeps "${TEX}" | xargs -n 1 -I % rsync -q --relative % "${TMPDIR}"
    BIB=$(grep '\\bibliography' manuscript.tex | cut -d '{' -f 2 | sed 's+}+.bib+')
    if [[ -f "$BIB" ]] ; then
      echo "${POWDER_BLUE}Adding ${BIB}${RS}"
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
  cataux # Cat any aux files required to render the tex file for portability
  catclass  # Cat the custom class file into the tex file for portability
  echo "${LIME_YELLOW}Removing comments from *.tex${RS}"
  printf '%s\0' *.tex | xargs -0 -n 1 sed -i.bak '/^%.*$/d'
  flattendirs # Get rid of graphicspath and flatten directory structure
  checktex # Make sure the cleaned tex files are OK
  texok=$?
  [[ $FORCE == 1 ]] && texok=0
  # Cleanup
  while read todel; do
    rm "$todel"
  done < <(cat .todel)
  rm *.out *.bak .todel 2>/dev/null

  if [[ $ZIP == 1 ]] && [[ $texok == 0 ]]; then
    echo "${POWDER_BLUE}Compressing files to ${OUTDIR}/${BASENAME}.zip${RS}"
    zip -r9 "${OUTDIR}/${BASENAME}.zip" *
  fi
  if [[ $BZ == 1 ]] && [[ $texok == 0 ]]; then
    echo "${POWDER_BLUE}Compressing files to ${OUTDIR}/${BASENAME}.tar.bz2${RS}"
    tar -cjvf "${OUTDIR}/${BASENAME}.tar.bz2" *
  fi
  cd ..
  rm -fr "${TMPDIR}"
else
  echo "${RED}Error enterting temp dir ${TMPDIR}${RS}"
  exit 1
fi

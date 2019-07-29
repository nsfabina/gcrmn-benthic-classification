#!/usr/bin/env bash

for MODEL in `ls models`; do
  for RESPONSE_MAPPING in `ls models/${MODEL}`; do
    LOCK="models/${MODEL}/${RESPONSE_MAPPING}/classify.lock"
    JOB_NAME="${MODEL}_${RESPONSE_MAPPING}"
    FOUND=$(squeue -u nfabina -o %j | grep ${JOB_NAME})
    if [[ ${FOUND} != ${JOB_NAME} ]] && [[ -f ${LOCK} ]]; then
      rm -f ${LOCK}
    fi
  done
done


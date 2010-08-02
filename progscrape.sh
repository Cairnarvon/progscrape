# bash auto-completion for progscrape
# Put this file (or a link to it) in /etc/bash_completion.d/ 

__progscrape()
{
    local cur prev

    COMPREPLY=()
    cur=${COMP_WORDS[COMP_CWORD]}
    prev=${COMP_WORDS[COMP_CWORD-1]}

    case $prev in
        --base-url)
            COMPREPLY=( $( compgen -W 'http://dis.4chan.org' -- $cur ) )
            return 0
            ;;
        --board)
            COMPREPLY=( $( compgen -W \
                '/lounge/ /vip/ /newnew/ /newpol/ /lang/ /sci/ /tech/ /food/ \
                /sports/ /comp/ /prog/ /img/ /sjis/ /tele/ /book/ /music/ \
                /anime/ /carcom/ /games/' -- $cur ) )
            return 0
            ;;
    esac

    if [[ "$cur" == -* ]]; then
        COMPREPLY=( $( compgen -W '--json --no-json \
            --html --no-html \
            --progress-bar --no-progress-bar \
            --verify-trips --no-verify-trips \
            --base-url --port --board \
            --aborn --no-aborn --partial \
            --help -h' -- $cur ) )
    elif [ ! -z $(type -t _filedir) ]; then
        _filedir db
    fi
}
complete -F __progscrape $filenames progscrape
complete -F __progscrape $filenames progscrape.py

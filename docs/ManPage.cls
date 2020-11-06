\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ManPage}[2017/01/25 v1.0 ManPage Documentation class]

\DeclareOption{twocolumn}{\OptionNotUsed}
\DeclareOption{letterpaper}{\OptionNotUsed}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[letterpaper]{article}

\RequirePackage[top=1in,left=0.75in,right=0.55in,bottom=1in,dvips]{geometry}
\RequirePackage{xcolor}
\RequirePackage{listings}
\RequirePackage{courier}
\RequirePackage{fancyhdr}
\RequirePackage{enumitem}
\RequirePackage{xparse}


\setlist{labelindent=0.1in ,labelwidth=2.75in, labelsep*=1em, %
  leftmargin =! , itemindent = 0pt, parsep=0in,style = nextline}
%\setlist{leftmargin=0in,%
%  itemsep=0pt,topsep=0pt,parsep=0pt,partopsep=0pt,itemindent=0.25in,%
%  ,labelsep*=.25in,style=sameline}
%\setlist{labelindent=1em ,labelwidth=1.3cm, labelsep*=1em, %
%  leftmargin=!,style = standard}% 
%\setlist[description]{leftmargin=.25in,itemindent%
%   itemsep=0pt,topsep=0pt,parsep=0pt,partopsep=0pt}

 
\setlength{\parindent}{0em}
\setlength{\parskip}{1em}
%\renewcommand{\baselinestretch}{2.0}



\colorlet{punct}{red!60!black}
\definecolor{background}{HTML}{F4F4F4}
\definecolor{delim}{RGB}{20,105,176}
\colorlet{numb}{magenta!60!black}

\lstdefinelanguage{json}{
    basicstyle=\normalfont\ttfamily,
    numbers=left,
    numberstyle=\scriptsize,
    stepnumber=1,
    numbersep=8pt,
    aboveskip=8pt,
    columns=fixed,
    showstringspaces=false,
    breaklines=true,
    backgroundcolor=\color{background},
    literate=
     *{0}{{{\color{numb}0}}}{1}
      {1}{{{\color{numb}1}}}{1}
      {2}{{{\color{numb}2}}}{1}
      {3}{{{\color{numb}3}}}{1}
      {4}{{{\color{numb}4}}}{1}
      {5}{{{\color{numb}5}}}{1}
      {6}{{{\color{numb}6}}}{1}
      {7}{{{\color{numb}7}}}{1}
      {8}{{{\color{numb}8}}}{1}
      {9}{{{\color{numb}9}}}{1}
      {:}{{{\color{punct}{:}}}}{1}
      {,}{{{\color{punct}{,}}}}{1}
      {\{}{{{\color{delim}{\{}}}}{1}
      {\}}{{{\color{delim}{\}}}}}{1}
      {[}{{{\color{delim}{[}}}}{1}
      {]}{{{\color{delim}{]}}}}{1},
}

\newcommand{\jsonsnippet}[1]{%
  %\begin{minipage}{\linewidth}%
  \lstinputlisting[language=json]{#1}%
  %\end{minipage}%
}

\makeatletter

\def\@version{\ClassError{ManPage}{Undefined \string\version}
  {You need to set \string\version{<VERSION>} before
    using \protect\version by itself}}

\NewDocumentCommand{\version}{g}{\IfNoValueTF{#1}{\@version}{\gdef\@version{#1}}}

\newcommand{\makeheaders}{
  \fancypagestyle{firstpage}{%
    \fancyhf{}%
    %\renewcommand{\footrulewidth}{0.1mm}%
    \fancyfoot[R]{\thepage}%
    \fancyfoot[C]{}%
    \fancyfoot[L]{}%
    \renewcommand{\headrulewidth}{0mm}%
  }

  %%\newcolumntype{P}[1]{>{\centering}p{#1}}
  \fancyhead[L]{\@date}%
  \fancyhead[C]{\@title}%
  \fancyhead[R]{\@version}%
  \fancyfoot[R]{\thepage}%
  \fancyfoot[C]{}%
  \fancyfoot[L]{}%
  \headheight 25pt
  
  \pagestyle{fancy}
}

\renewcommand{\maketitle}{
  \begin{centering}
    \vspace*{-1in}
    \LARGE \@title \\
    \large \@version \\
    \@date \\
  \end{centering}
  \makeheaders
  \thispagestyle{firstpage}
}

\makeatother


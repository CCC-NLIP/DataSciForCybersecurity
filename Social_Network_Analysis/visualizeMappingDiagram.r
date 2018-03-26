# This script can be used to visualize a mapping diagram using R googlevis Sankey. 
#It relies on data processed with the script createMappingDiagram.py

# Copyright (C) 2018 Sergio Pastrana (sp849@cam.ac.uk)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

rm(list = ls())
library(googleVis)
ce=read.csv('mapping.csv',header=TRUE)
sources=paste0(ce$source,'')
targets=paste0(ce$target,'')
ce$value=as.double(ce$value)

colormapl=c(H='red',G='blue',T='purple',C='brown',M='orange',E='green',B='gray',Y='pink',B='yellow',W='black',X='purple')
nodeOrder=unique(c(rbind(sources, targets)))
nodeColor=unname(colormapl[substring(nodeOrder, 1, 1)])

colors_node_array = paste0("[", paste0("'", nodeColor,"'", collapse = ','), "]")
ce$source=substring(ce$source,2)
ce$target=substring(ce$target,2)

#opts = paste0("{ node: { colors: ", colors_node_array ," } }" )
opts = paste0("{ link: { colorMode:'gradient' },node: {colors: ", colors_node_array ,",label: {fontSize: 12, bold: true}}}" )
s=gvisSankey(ce[,c('source','target','value')],options=list(height=350, sankey=opts))
print(s, file="mappingDiagram.html")
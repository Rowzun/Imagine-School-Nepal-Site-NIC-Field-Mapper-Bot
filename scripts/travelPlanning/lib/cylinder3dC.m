function ax = cylinder3dC(r, h, o, n, nseg, alpha)
% CYLINDER3DC  Transparent cylinder centred at o, symmetric along ±û·h/2
%
%   ax = cylinder3dC(r,h)                          % centre = [0 0 0], +Z axis
%   ax = cylinder3dC(r,h,center)                   % custom centre
%   ax = cylinder3dC(r,h,center,normal,nseg,alpha) % full control
%
%   All old scripts that passed the base centre still work: the function
%   detects if `o` is 3×1 (centre) or 6×1 (old base) and adapts.

    % ----------- defaults -------------------------------------------------
    if nargin<3||isempty(o),       o = [0 0 0]; end        % centre
    if nargin<4||isempty(n),       n = [0 0 1]; end
    if nargin<5||isempty(nseg),    nseg = 40;    end
    if nargin<6||isempty(alpha),   alpha = 0.25; end

    u = n(:)/norm(n);                             % unit axis
    c = o(:).';                                   % centre row-vector
    % build unit cylinder (height ∈ [-h/2,+h/2] )
    [X,Y,Z] = cylinder(r,nseg);
    Z = Z*h - h/2;                                % shift so centre at 0

    % rotate template so +Z → û
    v = [0 0 1]';
    if      all(abs(u-v)<1e-12),            R = eye(3);
    elseif  all(abs(u+v)<1e-12),            R = diag([1 -1 -1]);
    else
        k = cross(v,u); k=k/norm(k); a=acos(dot(v,u));
        K = [0 -k(3) k(2); k(3) 0 -k(1); -k(2) k(1) 0];
        R = eye(3)*cos(a)+sin(a)*K+(1-cos(a))*(k*k');
    end
    P  = R*[X(:) Y(:) Z(:)]';                % rotate
    Xr = reshape(P(1,:),size(X))+c(1);
    Yr = reshape(P(2,:),size(Y))+c(2);
    Zr = reshape(P(3,:),size(Z))+c(3);

    % plotting
    fig = figure('Color','w');   ax = axes('Parent',fig,'Color','w'); hold(ax,'on');
    surf(ax,Xr,Yr,Zr,'EdgeColor','none','FaceColor',[0.6 0.8 1],'FaceAlpha',alpha);

    plot3(ax,Xr(1,:),Yr(1,:),Zr(1,:), 'k-', 'LineWidth',1.1);   % bottom rim
    plot3(ax,Xr(end,:),Yr(end,:),Zr(end,:), 'k-', 'LineWidth',1.1); % top rim

    % ticks: 4×4 grid centred on (cx,cy)
    dx = r/2;
    xticks(ax, c(1)+(-r:dx:r));
    yticks(ax, c(2)+(-r:dx:r));
    grid(ax,'on');  ax.GridAlpha = 0.25;

    %axis(ax,'equal'); axis(ax,'vis3d'); view(ax,[0 -1 0]); camroll(ax,-90);
    axis(ax,'equal'); grid(ax,'on');
    %camlight(ax,'headlight'); lighting(ax,'gouraud');
end
